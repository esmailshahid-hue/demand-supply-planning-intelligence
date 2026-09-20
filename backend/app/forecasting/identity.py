"""Request-local reuse of unchanged Dataset JSON fields, never forecast/plan caching.

Dataset has no root/field JSON serializers. Field adapters preserve its exact
Pydantic JSON representation and field order. Regression tests compare the hash
against model_dump_json for every sample series and independent dataset mutations.
"""
from hashlib import sha256
import json
from pydantic import TypeAdapter
from backend.app.contracts import Dataset

_ADAPTERS={name:TypeAdapter(field.annotation) for name,field in Dataset.model_fields.items()}

class ProjectedIdentity:
    def __init__(self,data:Dataset):
        self.parts=[]
        for name,adapter in _ADAPTERS.items():
            key=json.dumps(name).encode()+b':'
            self.parts.append((name,key,None if name in ('demand_history','settings') else adapter.dump_json(getattr(data,name))))

    def hash(self,history,settings):
        digest=sha256();digest.update(b'{')
        for i,(name,key,value) in enumerate(self.parts):
            if i:digest.update(b',')
            digest.update(key)
            if value is None:value=_ADAPTERS[name].dump_json(history if name=='demand_history' else settings)
            digest.update(value)
        digest.update(b'}')
        return digest.hexdigest()
