"""Deterministic constrained order-up-to policy; no optimality claim."""
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from math import ceil, floor
from datetime import timedelta
from time import perf_counter
from backend.app.simulation.replay import cents, week


def benchmark(ctx, deadline=float('inf')):
    stock=dict(ctx.initial)
    receipts=defaultdict(float,ctx.receipts)
    commitments,payments,fees=defaultdict(int),defaultdict(int,ctx.existing),defaultdict(int)
    supplier_used,shared_used=defaultdict(int),defaultdict(float)
    purchases,movements=[],[]
    def room(loc,day):
        # Conservative receiving reservation: don't borrow future consumption to fit a delivery.
        used=sum((stock[p,loc]+ctx.unavailable[p,loc]+sum(receipts[p,loc,d] for d in range(i+1,day+1)))*ctx.products[p].volume_per_unit for p in ctx.products)
        return max(0.,ctx.locations[loc].storage_volume-used)
    def projected(key,until):
        value=stock[key]
        series=ctx.demand.get(key,[0.]*56)
        for d in range(i+1,until):
            value=max(0.,value+receipts[*key,d]-series[d])-ctx.dispatches[*key,d]
        return value+receipts[*key,until]
    def rank(key):
        a=ctx.assortment.get(key)
        remaining=stock[key]
        shortage=56
        for j in range(i+1,56):
            remaining+=receipts[*key,j]-ctx.demand.get(key,[0.]*56)[j]
            if remaining<0:
                shortage=j;break
        return shortage, not a.must_stock if a else True, a.service_class if a else 'C',key
    for i in range(56):
        if perf_counter()>=deadline:
            raise TimeoutError('Benchmark exhausted overall planning budget')
        day=ctx.day(i); w=week(day)
        for key in ctx.keys:
            stock[key]+=receipts[*key,i]
            stock[key]=max(0.,stock[key]-ctx.demand.get(key,[0.]*56)[i])
            stock[key]-=ctx.dispatches[*key,i]
        paid_lanes={(src,dst) for (src,dst,t),q in ctx.lane_used.items() if t==i and q>0}
        lane_used=defaultdict(float,{(s,d):q for (s,d,t),q in ctx.lane_used.items() if t==i})
        for key in sorted(ctx.assortment,key=rank):
            sku,dst=key
            for lane in sorted((l for l in ctx.data.transfer_lanes if l.destination==dst and sku in l.allowed_skus),key=lambda l:(l.transit_days,l.source)):
                arrival=i+lane.transit_days
                if arrival>=56 or day.weekday() not in lane.dispatch_weekdays or day.weekday() not in ctx.locations[lane.source].open_weekdays or ctx.day(arrival).weekday() not in ctx.locations[dst].open_weekdays:
                    continue
                if any(t.sku==sku and t.source==dst and t.destination==lane.source and t.dispatch_date==day for t in movements+list(ctx.data.open_transfers)):
                    continue
                target=sum(ctx.demand[key][arrival:min(56,arrival+7)])+ctx.buffers.get(key,0.)
                need=max(0.,target-projected(key,arrival))
                if need<=0: continue
                available=max(0.,stock[sku,lane.source]-ctx.reserve[sku,lane.source,i])
                pack=lane.pack_units
                requested=ceil(need/pack)*pack
                limits={
                    'DONOR_RESERVE_LIMIT' if ctx.locations[lane.source].kind=='store' else 'SHARED_STOCK_LIMIT':floor(available/pack)*pack,
                    'LANE_CAPACITY_LIMIT':floor(max(0,lane.capacity_units-lane_used[lane.source,dst])/pack)*pack,
                    'RECEIVING_SPACE_LIMIT':floor(room(dst,arrival)/ctx.products[sku].volume_per_unit/pack)*pack,
                }
                qty=min(requested,*limits.values())
                for code,limit in limits.items():
                    if limit<requested:
                        ctx.explain(code,f'{lane.source} → {dst}: requested {requested} units; this constraint permits at most {limit} pack-rounded units on this date.',sku=sku,location_id=dst,day=day)
                fee=0 if (lane.source,dst) in paid_lanes else cents(lane.grouped_dispatch_fee)
                b=ctx.budgets.get(w)
                if qty<=0 or not b or fees[w]+fee>cents(b.transfer_budget) or payments[w]+fee>cents(b.payment_ceiling):
                    if need>0:
                        if b and fees[w]+fee>cents(b.transfer_budget):
                            ctx.explain('TRANSFER_FUNDING_LIMIT','Remaining weekly movement allowance cannot pay this grouped dispatch fee.',sku=sku,location_id=dst,day=day)
                        if b and payments[w]+fee>cents(b.payment_ceiling):
                            ctx.explain('PAYMENT_CAPACITY_LIMIT','Existing and planned outflows leave insufficient payment capacity for this dispatch fee.',sku=sku,location_id=dst,day=day)
                    continue
                movements.append(ctx.movement(lane,sku,i,qty))
                stock[sku,lane.source]-=qty
                receipts[sku,dst,arrival]+=qty
                lane_used[lane.source,dst]+=qty
                fees[w]+=fee;payments[w]+=fee;paid_lanes.add((lane.source,dst))
        # Order stock for the next review/protection horizon, net of existing and proposed supply.
        skus=sorted(ctx.products,key=lambda sku:min((rank(k) for k in ctx.assortment if k[0]==sku),default=(56,True,'C',(sku,''))))
        for sku in skus:
            options=[]
            for o in ctx.data.supplier_offers:
                timing=ctx.timing(o,i) if o.sku==sku else None
                if timing:
                    options.append((o.price_per_base_unit,timing[1],o.offer_id,o,timing))
            shortage=min((rank(k)[0] for k in ctx.assortment if k[0]==sku),default=56)
            transit=max((l.transit_days for l in ctx.data.transfer_lanes if l.source==ctx.dc and sku in l.allowed_skus),default=1)
            on_time=[option for option in options if option[1]+transit<=shortage]
            if on_time:
                options=on_time
            elif options and shortage<56:
                ctx.explain('LEAD_TIME_SHORTFALL','No currently eligible source can reach the next shortage in time; later receipts can only cover later demand.',sku=sku,day=ctx.day(shortage))
            for _,_,_,o,(dispatch,arrival) in sorted(options):
                horizon=min(56,arrival+ctx.data.settings.review_period_days+max((l.transit_days for l in ctx.data.transfer_lanes if l.source==ctx.dc and sku in l.allowed_skus),default=1))
                expected=sum(sum(seq[i+1:horizon])+ctx.buffers.get(k,0.) for k,seq in ctx.demand.items() if k[0]==sku)
                available=sum(stock[sku,l]+sum(receipts[sku,l,d] for d in range(i+1,horizon)) for l in ctx.locations)
                need=max(0.,expected-available)
                if need<=0: break
                s=ctx.suppliers[o.supplier_id]
                pack=o.case_size; price=cents(o.price_per_base_unit)
                if price==0 and s.minimum_order_value>0:
                    ctx.explain('SUPPLIER_MINIMUM','A zero-price line cannot meet this supplier-order minimum on its own.',sku=sku,supplier_id=o.supplier_id,day=day)
                    continue
                minimum=max(o.moq_units,ceil(cents(s.minimum_order_value)/max(1,price)/pack)*pack,pack)
                qty=max(minimum,ceil(need/pack)*pack)
                cap=ctx.capacity.get((o.supplier_id,sku,dispatch),0)-supplier_used[o.supplier_id,sku,dispatch]
                unit=ctx.products[sku].volume_per_unit if s.shared_capacity_unit=='volume' else 1
                cap=min(cap,(s.shared_daily_capacity-shared_used[o.supplier_id,dispatch])/unit,room(ctx.dc,arrival)/ctx.products[sku].volume_per_unit)
                qty=min(qty,floor(max(0,cap)/pack)*pack)
                if qty<minimum:
                    ctx.explain('CAPACITY_BELOW_MINIMUM','Dated supplier/shared capacity or DC receiving space cannot support the case-rounded MOQ / supplier minimum.',sku=sku,supplier_id=o.supplier_id,day=day)
                    continue
                bw=week(ctx.day(arrival)+timedelta(days=o.balance_days_after_receipt))
                b,bb=ctx.budgets.get(w),ctx.budgets.get(bw)
                if not b or not bb: continue
                if price:
                    qty=min(qty,floor(max(0,cents(b.new_commitment_cap)-commitments[w])/price/pack)*pack)
                if qty<minimum:
                    ctx.explain('COMMITMENT_BELOW_MINIMUM','Remaining order-week commitment authority cannot fund a case-rounded MOQ / supplier minimum.',sku=sku,supplier_id=o.supplier_id,day=day)
                while qty>=minimum:
                    total=cents(o.price_per_base_unit*qty)
                    deposit=int((Decimal(total)*Decimal(str(o.deposit_fraction))).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
                    additions=defaultdict(int);additions[w]+=deposit;additions[bw]+=total-deposit
                    if all(payments[x]+v<=cents(ctx.budgets[x].payment_ceiling) for x,v in additions.items()): break
                    qty-=pack
                if qty<minimum:
                    ctx.explain('NO_FUNDED_ORDER','No order at or above the pack/MOQ/supplier minimum fits both commitment authority and dated deposit/balance payment capacity.',sku=sku,supplier_id=o.supplier_id,day=day)
                    continue
                purchases.append(ctx.purchase(o,i,qty))
                receipts[sku,ctx.dc,arrival]+=qty
                supplier_used[o.supplier_id,sku,dispatch]+=qty
                shared_used[o.supplier_id,dispatch]+=qty*unit
                commitments[w]+=total
                for x,v in additions.items(): payments[x]+=v
                break
    return purchases,movements
