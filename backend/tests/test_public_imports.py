"""Real fresh-process imports: public sample startup must not load file tooling."""
import json
import subprocess
import sys


def test_public_api_import_defers_private_file_and_solver_modules():
    result=subprocess.check_output([sys.executable,'-c',
        "import sys,json; from time import perf_counter; start=perf_counter(); "
        "import backend.app.main; print(json.dumps({'seconds':perf_counter()-start,"
        "'loaded':[m for m in ('openpyxl','numpy','scipy','backend.app.data.accepted',"
        "'backend.app.data.private_storage','unittest.mock') if m in sys.modules]}))"],text=True)
    value=json.loads(result)
    assert value['loaded']==[] and value['seconds']>0
