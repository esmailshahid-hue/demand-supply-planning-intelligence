"""Exact candidate locks shared by both planners and checked independently afterwards."""
from dataclasses import dataclass, field
from hashlib import sha256
import json
from backend.app.planning.contracts import Purchase, Movement, Failure


def business_key(action):
    fields = ('sku', 'supplier_id', 'offer_id', 'destination', 'order_date', 'dispatch_date', 'arrival_date') if isinstance(action, Purchase) else ('sku', 'source', 'destination', 'dispatch_date', 'arrival_date')
    values = [type(action).__name__, *[str(getattr(action, key)) for key in fields]]
    return sha256(json.dumps(values, separators=(',', ':')).encode()).hexdigest()


@dataclass
class ReviewConstraints:
    purchases: list[Purchase] = field(default_factory=list)
    movements: list[Movement] = field(default_factory=list)
    rejected: set[str] = field(default_factory=set)

    def locks(self):
        return {business_key(a): a for a in self.purchases+self.movements}

    def failures(self, purchases, movements):
        actions = {business_key(a): a for a in purchases+movements}
        failures = []
        for key, action in self.locks().items():
            actual = actions.get(key)
            if not actual or actual.model_dump(exclude={'action_id', 'reason'}) != action.model_dump(exclude={'action_id', 'reason'}):
                failures.append(Failure(code='review_lock_conflict', message='Exact reviewed terms or quantity could not be retained. Resolve the review conflict before acceptance.', action_id=action.action_id, sku=action.sku))
        for key in self.rejected & actions.keys():
            failures.append(Failure(code='review_rejection_conflict', message='A prohibited candidate remains in the plan.', action_id=actions[key].action_id))
        return failures
