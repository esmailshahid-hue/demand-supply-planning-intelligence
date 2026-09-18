"""Explicit refresh against a user-supplied accepted snapshot, without server history."""
from backend.app.contracts import Contract
from pydantic import Field
from backend.app.planning.contracts import Purchase, Failure
from backend.app.planning.constraints import ReviewConstraints, business_key
from backend.app.planning.review import ReviewConflict


class Execution(Contract):
    external_id: str
    confirmed_units: int = Field(ge=0,strict=True)
    executed_units: int = Field(ge=0,strict=True)


def reconcile(data,snapshot,executions):
    """Confirmed quantity = executed plus open remainder; only unconfirmed units stay proposed."""
    known={snapshot.external_ids[a.action_id]:a for a in snapshot.draft.result.proposed.purchases+snapshot.draft.result.proposed.movements}
    orders={a.external_id:a for a in data.open_orders};moves={a.external_id:a for a in data.open_transfers}
    used=set();constraints=ReviewConstraints();records=[]
    def conflict(code,message): raise ReviewConflict([Failure(code=code,message=message)])
    if any(key.startswith('DSP-') and key not in known for key in set(orders)|set(moves)):
        conflict('unknown_execution','Each exported DSP transaction must belong to the supplied accepted snapshot.')
    for row in executions:
        if row.external_id in used: conflict('duplicate_execution','Each external reconciliation ID must occur exactly once.')
        used.add(row.external_id)
        proposal=known.get(row.external_id)
        if proposal is None: conflict('unknown_execution','External ID is not present in the supplied accepted snapshot.')
        confirmed=(orders if isinstance(proposal,Purchase) else moves).get(row.external_id)
        if confirmed is None: conflict('missing_execution','Each execution record requires a matching confirmed/received transaction.')
        fields=('sku','supplier_id','destination','order_date','dispatch_date','arrival_date') if isinstance(proposal,Purchase) else ('sku','source','destination','dispatch_date','arrival_date')
        if any(getattr(proposal,f)!=getattr(confirmed,f) for f in fields): conflict('execution_terms','Confirmed transaction differs from exported business terms; resolve the conflict explicitly.')
        if isinstance(proposal,Purchase):
            offer=next(o for o in snapshot.dataset.supplier_offers if o.offer_id==proposal.offer_id)
            if confirmed.cost_per_base_unit!=offer.price_per_base_unit: conflict('execution_price','Confirmed price differs from the accepted commercial terms.')
        if row.confirmed_units>proposal.units or row.executed_units+confirmed.remaining_units!=row.confirmed_units:
            conflict('execution_quantity','Executed plus open remaining units must equal confirmed units, which cannot exceed the accepted proposal.')
        if confirmed.status=='received' and row.executed_units!=row.confirmed_units: conflict('execution_status','Received quantity must be fully executed and already represented in the new inventory snapshot.')
        remaining=proposal.units-row.confirmed_units
        if remaining:
            action=proposal.model_copy(deep=True);action.units=remaining
            if isinstance(action,Purchase):
                current=next((o for o in data.supplier_offers if o.offer_id==action.offer_id),None)
                terms=('supplier_id','sku','price_per_base_unit','case_size','moq_units','lead_time_days','dispatch_weekdays','order_weekdays','deposit_fraction','balance_days_after_receipt')
                if current is None or any(getattr(current,f)!=getattr(offer,f) for f in terms):
                    conflict('remaining_commercial_terms','The unconfirmed remainder must retain its accepted offer and commercial terms. Resolve changed terms before importing this remainder.')
                from backend.app.simulation.replay import cents
                from decimal import Decimal
                action.value=cents(Decimal(str(offer.price_per_base_unit))*remaining)/100
                constraints.purchases.append(action)
            else: constraints.movements.append(action)
        else: constraints.rejected.add(business_key(proposal))
        records.append({'external_id':row.external_id,'accepted_units':proposal.units,'confirmed_units':row.confirmed_units,'executed_units':row.executed_units,'open_units':confirmed.remaining_units,'remaining_proposal_units':remaining})
    matching=set(known)&(set(orders)|set(moves))
    if matching-used: conflict('ambiguous_execution','Provide explicit confirmed and executed quantities for every matching exported external ID.')
    return constraints,records
