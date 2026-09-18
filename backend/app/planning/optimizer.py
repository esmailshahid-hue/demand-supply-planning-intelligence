"""Full-horizon joint case/pack MILP with staged service objectives.

No forecast is produced here. No solver feasibility flag is trusted by the API.
"""
from collections import defaultdict
from datetime import timedelta
from math import floor, ceil, isfinite
from time import perf_counter
import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.sparse import coo_matrix
from backend.app.planning.contracts import SolverStage
from backend.app.simulation.replay import cents, week
from backend.app.planning.constraints import business_key


class Model:
    def __init__(self, deadline=float('inf')):
        self.deadline=deadline
        self.upper=[];self.integer=[];self.rows=[];self.lo=[];self.hi=[]

    def check_deadline(self):
        if perf_counter()>=self.deadline:
            raise TimeoutError('Joint model budget exhausted')

    def var(self, upper=np.inf, integer=False):
        if len(self.upper)%256==0:self.check_deadline()
        j=len(self.upper);self.upper.append(max(0,upper));self.integer.append(int(integer));return j

    def row(self, terms, lo=-np.inf, hi=np.inf):
        if len(self.rows)%256==0:self.check_deadline()
        self.rows.append({j:v for j,v in terms.items() if v});self.lo.append(lo);self.hi.append(hi)

    def solve(self, objective, seconds):
        deadline=min(self.deadline,perf_counter()+seconds)
        self.check_deadline()
        rr=[];cc=[];vv=[]
        for i,row in enumerate(self.rows):
            if i%256==0:self.check_deadline()
            for j,v in row.items():rr.append(i);cc.append(j);vv.append(v)
        mat=coo_matrix((vv,(rr,cc)),shape=(len(self.rows),len(self.upper))).tocsc()
        costs=np.zeros(len(self.upper))
        for j,v in objective.items():costs[j]=v
        integrality=np.array(self.integer);bounds=Bounds(np.zeros(len(self.upper)),self.upper)
        constraints=LinearConstraint(mat,self.lo,self.hi)
        remaining=deadline-perf_counter()
        if remaining<=0:raise TimeoutError('Joint matrix preparation exhausted budget')
        return milp(costs, integrality=integrality, bounds=bounds,
            constraints=constraints,options={'time_limit':remaining,'mip_rel_gap':0.,'presolve':True})


def optimize(ctx, deadline):
    started=perf_counter()
    try:return _optimize(ctx,deadline)
    except TimeoutError:
        # Construction never releases partial actions. The engine replays its benchmark.
        return [],[],[SolverStage(name='model_build',status='time_limit',elapsed_ms=(perf_counter()-started)*1000)]


def _optimize(ctx, deadline):
    model=Model(deadline)
    arriving,outgoing=defaultdict(dict),defaultdict(dict)
    purchase_vars,movement_vars=[],[]
    commitments,payments,fees=defaultdict(dict),defaultdict(dict),defaultdict(dict)
    cap_rows,shared_rows,lane_rows=defaultdict(dict),defaultdict(dict),defaultdict(dict)
    order_groups,fee_groups={},{}
    move_flags=defaultdict(list)
    donor_flags=defaultdict(list)
    cost={};ties={}
    locks=ctx.review.locks()
    represented=set()
    for i in range(56):
        if perf_counter()>=deadline: return [],[],[SolverStage(name='model_build',status='time_limit',elapsed_ms=0)]
        day=ctx.day(i);w=week(day)
        for o in sorted(ctx.data.supplier_offers,key=lambda x:x.offer_id):
            timing=ctx.timing(o,i)
            if not timing:continue
            dispatch,arrival=timing
            maximum=ctx.capacity.get((o.supplier_id,o.sku,dispatch),0)//o.case_size
            if maximum<=0:continue
            pack=o.case_size
            q=model.var(maximum,True);active=model.var(1,True)
            key=business_key(ctx.purchase(o,i,pack))
            if key in ctx.review.rejected: model.row({q:1},lo=0,hi=0)
            if key in locks:
                quantity=locks[key].units/pack
                model.row({q:1},lo=quantity,hi=quantity);represented.add(key)
            model.row({q:1,active:-maximum},hi=0)
            model.row({q:1,active:-max(1,ceil(o.moq_units/pack))},lo=0)
            group=o.supplier_id,i
            if group not in order_groups:order_groups[group]=(model.var(1,True),{})
            flag,values=order_groups[group]
            model.row({active:1,flag:-1},hi=0)
            price=cents(o.price_per_base_unit)*pack
            values[q]=price
            arriving[o.sku,ctx.dc,arrival][q]=pack
            commitments[w][q]=price
            bw=week(ctx.day(arrival)+timedelta(days=o.balance_days_after_receipt))
            deposit=model.var(price*maximum,True)
            model.row({deposit:1,q:-price*o.deposit_fraction},lo=-.499999,hi=.5)
            payments[w][deposit]=payments[w].get(deposit,0)+1
            payments[bw][q]=payments[bw].get(q,0)+price
            payments[bw][deposit]=payments[bw].get(deposit,0)-1
            cap_rows[o.supplier_id,o.sku,dispatch][q]=pack
            s=ctx.suppliers[o.supplier_id]
            shared_rows[o.supplier_id,dispatch][q]=pack*(ctx.products[o.sku].volume_per_unit if s.shared_capacity_unit=='volume' else 1)
            cost[q]=price/100;ties[q]=len(purchase_vars)+1
            purchase_vars.append((q,o,i))
        for lane in sorted(ctx.data.transfer_lanes,key=lambda l:(l.source,l.destination)):
            arrival=i+lane.transit_days
            if arrival>=56 or day.weekday() not in lane.dispatch_weekdays or day.weekday() not in ctx.locations[lane.source].open_weekdays or ctx.day(arrival).weekday() not in ctx.locations[lane.destination].open_weekdays:continue
            maximum=max(0,lane.capacity_units-ctx.lane_used[lane.source,lane.destination,i])//lane.pack_units
            if maximum<=0:continue
            group=lane.source,lane.destination,i
            fg=model.var(1,True);fee_groups[group]=(fg,[])
            fee=0 if ctx.lane_used[lane.source,lane.destination,i]>0 else cents(lane.grouped_dispatch_fee)
            payments[w][fg]=fee;fees[w][fg]=fee;cost[fg]=fee/100
            for sku in sorted(lane.allowed_skus):
                q=model.var(maximum,True);active=model.var(1,True)
                model.row({q:1,active:-maximum},hi=0);model.row({q:1,active:-1},lo=0)
                model.row({active:1,fg:-1},hi=0)
                fee_groups[group][1].append(active)
                pack=lane.pack_units
                key=business_key(ctx.movement(lane,sku,i,pack))
                if key in ctx.review.rejected: model.row({q:1},lo=0,hi=0)
                if key in locks:
                    quantity=locks[key].units/pack
                    model.row({q:1},lo=quantity,hi=quantity);represented.add(key)
                outgoing[sku,lane.source,i][q]=pack
                arriving[sku,lane.destination,arrival][q]=pack
                lane_rows[group][q]=pack
                move_flags[sku,lane.source,lane.destination,i].append(active)
                donor_flags[sku,lane.source,i].append(active)
                ties[q]=len(movement_vars)+1
                movement_vars.append((q,lane,sku,i))
    if set(locks)-represented:
        return [],[],[SolverStage(name='review_locks',status='infeasible',elapsed_ms=0)]
    for (sid,i),(flag,values) in order_groups.items():
        minimum=cents(ctx.suppliers[sid].minimum_order_value)
        model.row({**values,flag:-minimum},lo=0)
        model.row({**values,flag:-sum(v*model.upper[q] for q,v in values.items())},hi=0)
    for flag,actives in fee_groups.values():model.row({flag:1,**{a:-1 for a in actives}},hi=0)
    for key,terms in cap_rows.items():model.row(terms,hi=ctx.capacity[key])
    for (sid,i),terms in shared_rows.items():model.row(terms,hi=ctx.suppliers[sid].shared_daily_capacity)
    for (src,dst,i),terms in lane_rows.items():
        lane=next(l for l in ctx.data.transfer_lanes if (l.source,l.destination)==(src,dst))
        model.row(terms,hi=lane.capacity_units-ctx.lane_used[src,dst,i])
    for w in set(commitments)|set(payments)|set(fees):
        b=ctx.budgets.get(w)
        model.row(commitments[w],hi=cents(b.new_commitment_cap) if b else 0)
        model.row(payments[w],hi=cents(b.payment_ceiling)-ctx.existing[w] if b else 0)
        model.row(fees[w],hi=cents(b.transfer_budget) if b else 0)
    for (sku,src,dst,i),flags in move_flags.items():
        opposing=move_flags.get((sku,dst,src,i),[])
        existing=any(t.sku==sku and t.source==dst and t.destination==src and t.status=='confirmed' and t.dispatch_date==ctx.day(i) for t in ctx.data.open_transfers)
        model.row({a:1 for a in flags+opposing},hi=0 if existing else 1)
    stock,served={},{}
    peak_rows=defaultdict(dict)
    buffer_objective={}
    for sku,loc in ctx.keys:
        key=sku,loc
        volume=ctx.products[sku].volume_per_unit
        upper=ctx.locations[loc].storage_volume/volume
        for i in range(56):
            s=model.var(upper);stock[*key,i]=s
            d=ctx.demand.get(key,[0.]*56)[i]
            f=model.var(d);served[*key,i]=f
            terms={s:1,f:1,**outgoing[*key,i]}
            if i:terms[stock[*key,i-1]]=-1
            for q,v in arriving[*key,i].items():terms[q]=terms.get(q,0)-v
            rhs=ctx.receipts[*key,i]-ctx.dispatches[*key,i]+(ctx.initial[key] if i==0 else 0)
            model.row(terms,lo=rhs,hi=rhs)
            # Service must equal min(pre-dispatch usable stock, daily demand).
            if d>0:
                shortage=model.var(1,True)
                model.row({f:1,shortage:d},lo=d)
                model.row({s:1,shortage:upper,**outgoing[*key,i]},hi=upper-ctx.dispatches[*key,i])
            peak_rows[loc,i][s]=volume;peak_rows[loc,i][f]=volume
            for q,v in outgoing[*key,i].items():peak_rows[loc,i][q]=v*volume
            if ctx.locations[loc].kind=='store':
                for a in donor_flags[sku,loc,i]:model.row({s:1,a:-ctx.reserve[*key,i]},lo=0)
                if ctx.dispatches[*key,i]:model.row({s:1},lo=ctx.reserve[*key,i])
                if (i+1)%7==0:
                    b=model.var(ctx.buffers.get(key,0.));model.row({s:1,b:1},lo=ctx.buffers.get(key,0.));buffer_objective[b]=1
            cost[s]=ctx.products[sku].cost_per_base_unit*ctx.data.settings.annual_holding_rate/365
    for (loc,i),terms in peak_rows.items():
        fixed=sum((ctx.unavailable[p,loc]+ctx.dispatches[p,loc,i])*ctx.products[p].volume_per_unit for p in ctx.products)
        model.row(terms,hi=ctx.locations[loc].storage_volume-fixed)
    objectives=[]
    # Target shortfall is aggregated from units within each class/store, not mean SKU percentages.
    for window,indices in [('visible',range(28)),('tail',range(28,56))]:
        for priority in ['must_stock','A','B','C']:
            objective={}
            for loc in sorted(ctx.locations):
                for cls in 'ABC':
                    members=[k for k,a in ctx.assortment.items() if k[1]==loc and a.service_class==cls and (a.must_stock if priority=='must_stock' else not a.must_stock and cls==priority)]
                    if not members:continue
                    total=sum(sum(ctx.demand[k][i] for i in indices) for k in members)
                    target=total*ctx.data.settings.class_targets[cls]
                    short=model.var(target);objective[short]=1
                    model.row({short:1,**{served[*k,i]:1 for k in members for i in indices}},lo=target)
            if objective:objectives.append((window+'_'+priority,objective))
    objectives.extend([('weekly_buffer_deficit',buffer_objective),('commitment_movement_holding',cost),('stable_action_ties',ties)])
    stages=[];incumbent=None
    for name,objective in objectives:
        remaining=deadline-perf_counter()
        if remaining<=.01:
            stages.append(SolverStage(name=name,status='time_limit',elapsed_ms=0));break
        started=perf_counter()
        try:result=model.solve(objective,remaining)
        except TimeoutError:
            stages.append(SolverStage(name=name,status='time_limit',elapsed_ms=(perf_counter()-started)*1000))
            return [],[],stages
        stages.append(SolverStage(name=name,status={0:'optimal',1:'time_limit',2:'infeasible',3:'unbounded',4:'error'}.get(result.status,'error'),
            objective=float(result.fun) if result.fun is not None and isfinite(result.fun) else None,
            gap=float(result.mip_gap) if getattr(result,'mip_gap',None) is not None and isfinite(result.mip_gap) else None,elapsed_ms=(perf_counter()-started)*1000))
        if result.x is not None:incumbent=result.x
        if result.status!=0:break
        model.row(objective,hi=result.fun+1e-6)
    if incumbent is None:return [],[],stages
    purchases=[ctx.purchase(o,i,round(incumbent[q])*o.case_size) for q,o,i in purchase_vars if incumbent[q]>.5]
    movements=[ctx.movement(l,sku,i,round(incumbent[q])*l.pack_units) for q,l,sku,i in movement_vars if incumbent[q]>.5]
    return purchases,movements,stages
