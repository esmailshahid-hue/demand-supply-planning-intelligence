"""Transport projection only. Full independently replayed results stay authoritative."""
from backend.app.planning.contracts import PlanResult


def decisions(result: PlanResult, include_stock=False) -> PlanResult:
    if include_stock:
        return result
    policies = {}
    for name in ('proposed', 'benchmark', 'no_action'):
        policy = getattr(result, name)
        if policy is not None:
            policies[name] = policy.model_copy(update={
                'replay': policy.replay.model_copy(update={'stock': []})})
    return result.model_copy(update={**policies, 'stock_detail': 'on_demand',
        'stock_row_count': len(result.proposed.replay.stock) if result.proposed else 0})
