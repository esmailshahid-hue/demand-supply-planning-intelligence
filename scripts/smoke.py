"""Production HTTP smoke test; run after scripts/start.sh or against a container."""
import argparse
import json
from time import perf_counter
from urllib.request import Request, urlopen

parser = argparse.ArgumentParser()
parser.add_argument("--url", default="http://127.0.0.1:8000")
args = parser.parse_args()

def request(path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    with urlopen(Request(args.url+path, data=data, headers={"Content-Type":"application/json"}),timeout=40) as response:
        assert response.status == 200
        return response.read()

assert json.loads(request("/api/health"))["status"] == "ok"
assert b'<div id="root"></div>' in request("/")
for size in ("fixture","full"):
    for run in ("cold","warm"):
        start = perf_counter()
        result = json.loads(request("/api/forecast/sample",{"size":size}))
        assert len(result["forecast"]) == 56
        assert result["visible_units"] == sum(p["forecast_units"] for p in result["forecast"][:28])
        assert len(result["selection"]) == len(result["final_check"]) == 3
        assert len({r["method"] for r in result["selection"]}) == 3
        assert all(p["provisional_tail"] for p in result["forecast"][28:])
        print(f'{size} {run}: HTTP {perf_counter()-start:.3f}s; engine {result["elapsed_ms"]:.1f}ms; {result["selected_method"]}; {result["status"]}')
print("Production HTTP smoke passed: built frontend, health, fixture and full-sample live calculations.")
