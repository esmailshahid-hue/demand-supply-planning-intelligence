from collections import defaultdict
from datetime import timedelta
from hashlib import sha256
from time import perf_counter
from backend.app.forecasting.engine import forecast
from backend.app.planning.contracts import ForecastTrace, Purchase, Movement, Failure
from backend.app.simulation.replay import cents, week


class Inputs:
    def __init__(self, data, demand, buffers, review=None):
        from backend.app.planning.constraints import ReviewConstraints
        self.review = review or ReviewConstraints()
        self.data, self.demand, self.buffers = data, demand, buffers
        self.exceptions = {}
        self.start = data.settings.as_of
        self.h = 56
        self.products = {p.sku:p for p in data.products}
        self.locations = {l.location_id:l for l in data.locations}
        self.dc = next(l.location_id for l in data.locations if l.kind == 'dc')
        self.keys = [(p,l) for p in sorted(self.products) for l in sorted(self.locations)]
        self.assortment = {(a.sku,a.location_id):a for a in data.assortment}
        self.initial = {k:0. for k in self.keys}
        self.unavailable = {k:0. for k in self.keys}
        for r in data.inventory:
            self.initial[r.sku,r.location_id] = r.on_hand-r.blocked-r.reserved
            self.unavailable[r.sku,r.location_id] = r.blocked+r.reserved
        self.receipts, self.dispatches = defaultdict(float), defaultdict(float)
        self.lane_used = defaultdict(float)
        for o in data.open_orders:
            if o.status != 'received':
                self.receipts[o.sku,o.destination,(o.arrival_date-self.start).days] += o.remaining_units
        for t in data.open_transfers:
            if t.status != 'received':
                self.receipts[t.sku,t.destination,(t.arrival_date-self.start).days] += t.remaining_units
                if t.status == 'confirmed':
                    i = (t.dispatch_date-self.start).days
                    self.dispatches[t.sku,t.source,i] += t.remaining_units
                    self.lane_used[t.source,t.destination,i] += t.remaining_units
        self.capacity = {(c.supplier_id,c.sku,(c.dispatch_date-self.start).days):c.available_units for c in data.supplier_capacity}
        self.suppliers = {s.supplier_id:s for s in data.suppliers}
        self.budgets = {b.week_start:b for b in data.budgets}
        self.existing = defaultdict(int)
        for p in data.payables:
            self.existing[week(p.due_date)] += cents(p.amount)
        self.reserve = {}
        for key in self.keys:
            seq = self.demand.get(key,[0.]*56)
            for i in range(56):
                cum = peak = 0.
                for j in range(i+1,i+8):
                    cum += seq[j if j<56 else 49+(j-56)%7] - self.receipts[*key,j]
                    peak = max(peak,cum)
                self.reserve[*key,i] = peak+self.buffers.get(key,0.) if self.locations[key[1]].kind=='store' else 0.

    def day(self, i):
        return self.start + timedelta(days=i)

    def explain(self, code, message, **scope):
        key=(code,scope.get('sku'),scope.get('location_id'),scope.get('supplier_id'))
        if key not in self.exceptions:
            self.exceptions[key]=Failure(code=code,message=message,**scope)

    def timing(self, offer, i):
        day = self.day(i)
        if day.weekday() not in offer.order_weekdays or not offer.valid_from<=day<=offer.valid_to:
            return None
        d = i
        while self.day(d).weekday() not in offer.dispatch_weekdays:
            d += 1
        a = d+offer.lead_time_days
        while self.day(a).weekday() not in self.locations[self.dc].open_weekdays:
            a += 1
        if a>=56 or self.day(d)>offer.valid_to:
            return None
        return d,a

    def purchase(self, o, i, units):
        d,a = self.timing(o,i)
        return Purchase(action_id=f'P-{o.offer_id}-{i}', offer_id=o.offer_id, sku=o.sku, supplier_id=o.supplier_id,
            destination=self.dc,units=int(units),order_date=self.day(i),dispatch_date=self.day(d),arrival_date=self.day(a),
            value=cents(o.price_per_base_unit*units)/100)

    def movement(self, lane, sku, i, units):
        return Movement(action_id=f'T-{sku}-{lane.source}-{lane.destination}-{i}',sku=sku,source=lane.source,destination=lane.destination,
            units=int(units),dispatch_date=self.day(i),arrival_date=self.day(i+lane.transit_days))


def network_forecasts(data, deadline):
    """Invoke the unchanged Pass 1 evaluator on each series, retaining all relevant input fields.

    Partition only history to avoid serializing 99k irrelevant rows 240 times.
    Trace hashes refer to this series projection; the plan has the complete input hash.
    """
    rows = defaultdict(list)
    for r in data.demand_history:
        rows[r.sku,r.location_id].append(r)
    offers = defaultdict(list)
    for offer in data.supplier_offers:
        offers[offer.sku].append(offer)
    direct_lanes = defaultdict(list)
    dcs = {location.location_id for location in data.locations if location.kind == 'dc'}
    for lane in data.transfer_lanes:
        if lane.source in dcs:
            direct_lanes[lane.destination].append(lane)
    demand, buffers, trace, failures = {}, {}, [], []
    for a in sorted(data.assortment,key=lambda a:(a.sku,a.location_id)):
        key = a.sku,a.location_id
        # The declared protection_days remains a floor. Review + worst eligible supplier
        # replenishment path to this store (including calendar wait) determines evidence.
        days = data.settings.protection_days
        direct = [lane for lane in direct_lanes[a.location_id] if a.sku in lane.allowed_skus]
        valid_paths = []
        for o in offers[a.sku]:
            for lane in direct:
                for i in range(7):
                    origin=data.settings.as_of+timedelta(days=i)
                    arrival=_valid_path_arrival(data,o,lane,origin)
                    if arrival is not None:
                        valid_paths.append((origin,arrival))
        if not valid_paths:
            failures.append(Failure(code='no_valid_replenishment_path',message='No supplier offer and DC-to-store lane can be ordered and dispatched within its validity and receiving calendars.',sku=a.sku,location_id=a.location_id))
            continue
        for origin,arrival in valid_paths:
            days=max(days,(arrival-origin).days+data.settings.review_period_days)
        if days>28:
            failures.append(Failure(code='protection_envelope', message='Review plus calendar-adjusted replenishment exceeds supported 28-day evidence; extend the model explicitly.',sku=a.sku,location_id=a.location_id))
            continue
        if perf_counter()>=deadline:
            raise TimeoutError('Network forecast budget exhausted')
        settings=data.settings.model_copy(update={'protection_days':days})
        projected=data.model_copy(update={'demand_history':rows[key], 'settings':settings})
        result=forecast(projected,*key,runtime_seconds=max(.01,deadline-perf_counter()))
        if result.status=='unavailable' or result.buffer.units is None:
            failures.append(Failure(code='forecast_unavailable',message='A defensible forecast and buffer are required for every ranged series.',sku=a.sku,location_id=a.location_id))
            continue
        demand[key]=[p.forecast_units for p in result.forecast]
        buffers[key]=result.buffer.units
        trace.append(ForecastTrace(sku=a.sku,location_id=a.location_id,run_id=result.run_id,input_hash=result.input_hash,
            method=result.selected_method,status=result.status,buffer=result.buffer))
    return demand,buffers,trace,failures


def _valid_path_arrival(data, offer, lane, origin):
    """Return the first store receipt for an offer that is orderable at origin."""
    if not offer.valid_from<=origin<=offer.valid_to:
        return None
    dc=next(l for l in data.locations if l.location_id==lane.source and l.kind=='dc')
    store=next(l for l in data.locations if l.location_id==lane.destination)
    order=origin
    while order<=offer.valid_to and order.weekday() not in offer.order_weekdays:
        order+=timedelta(days=1)
    if order>offer.valid_to:
        return None
    dispatch=order
    while dispatch<=offer.valid_to and dispatch.weekday() not in offer.dispatch_weekdays:
        dispatch+=timedelta(days=1)
    if dispatch>offer.valid_to:
        return None
    received=dispatch+timedelta(days=offer.lead_time_days)
    while received.weekday() not in dc.open_weekdays:
        received+=timedelta(days=1)
    lane_dispatch=received
    # Weekday calendars repeat every seven days. Four weeks is a bounded
    # impossibility check, not a lead-time shortcut.
    for _ in range(28):
        arrival=lane_dispatch+timedelta(days=lane.transit_days)
        if (lane_dispatch.weekday() in lane.dispatch_weekdays
                and lane_dispatch.weekday() in dc.open_weekdays
                and arrival.weekday() in store.open_weekdays):
            return arrival
        lane_dispatch+=timedelta(days=1)
    return None


def planning_input_failures(data):
    failures=[]
    def add(code,message,**scope): failures.append(Failure(code=code,message=message,**scope))
    snapshots={(r.sku,r.location_id) for r in data.inventory}
    for o in data.supplier_offers:
        if abs(o.price_per_base_unit*100-cents(o.price_per_base_unit))>1e-7:
            add('money_precision','Supply prices must be normalized to SAR cents per base unit before planning.',sku=o.sku,supplier_id=o.supplier_id)
    for p in data.products:
        for l in data.locations:
            if (p.sku,l.location_id) not in snapshots:
                add('missing_snapshot','Every product/location needs an explicit stock snapshot, including zero.',sku=p.sku,location_id=l.location_id)
    capacity={(r.supplier_id,r.sku,r.dispatch_date) for r in data.supplier_capacity}
    for o in data.supplier_offers:
        for i in range(56):
            day=data.settings.as_of+timedelta(days=i)
            if o.valid_from<=day<=o.valid_to and day.weekday() in o.dispatch_weekdays and (o.supplier_id,o.sku,day) not in capacity:
                add('missing_capacity','Explicit dated remaining supplier availability is required; missing is not unlimited.',sku=o.sku,supplier_id=o.supplier_id,day=day)
                break
    for s in data.suppliers:
        if s.shared_daily_capacity is None:
            add('missing_shared_capacity','Declare a finite shared supplier capacity for planning.',supplier_id=s.supplier_id)
    for l in data.transfer_lanes:
        if l.capacity_units is None:
            add('missing_lane_capacity','Declare a finite shared lane capacity.',location_id=l.source)
    for p in data.payables:
        if p.due_date<data.settings.as_of:
            add('overdue_payable','Correct the due date of overdue unpaid obligations before funded planning.',day=p.due_date)
    for b in data.budgets:
        due=sum(cents(p.amount) for p in data.payables if week(p.due_date)==b.week_start)
        if due>cents(b.payment_ceiling):
            add('existing_payment_breach',f'Existing unpaid obligations exceed this payment ceiling by SAR {(due-cents(b.payment_ceiling))/100:.2f}; new recommendations cannot remove the breach.',day=b.week_start)
    for t in data.open_transfers:
        if (t.status=='confirmed' and t.dispatch_date<data.settings.as_of) or (t.status=='dispatched' and t.dispatch_date>=data.settings.as_of):
            add('transaction_status','Transfer status and as-of snapshot do not agree.',action_id=t.external_id)
    if data.settings.funding_mode!='funded':
        add('unfunded','Funding data is required for executable recommendations.')
    return failures
