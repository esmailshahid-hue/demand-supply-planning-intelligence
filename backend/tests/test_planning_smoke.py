"""A slow/invalid response must retain diagnostics and not suppress later runs."""
import json
from contextlib import contextmanager
from urllib.error import URLError

import pytest
from scripts import planning_smoke as smoke


def response(size):
    count=40 if size=='fixture' else 240
    policy={'purchases':[{'units':1,'value':10}], 'movements':[{'units':1}],
        'replay':{'feasible':True,'failures':[], 'summary':{'commitments':10,'payments':5},
            'stock':[{}]*(56*(count+count//4)), 'payments':[{'amount':5}],
            'cash':[{'commitment_headroom':0,'payment_headroom':1,'transfer_headroom':2}]}}
    return {'status':'feasible_fallback','proposed':policy,'benchmark':policy,'no_action':policy,
        'exceptions':[],'forecasts':[{}]*count,'elapsed_ms':123,'challenger_budget_seconds':2 if size=='fixture' else 0,
        'stages':[{'name':'visible_must_stock','status':'time_limit'},
                  {'name':'independent_fallback','status':'benchmark'}]}


@pytest.mark.parametrize('fault',['slow','invalid','malformed','transport','changed'])
def test_smoke_reports_all_requests_and_fails(monkeypatch,capsys,fault):
    calls=[];clock=[0.]
    @contextmanager
    def request(req,timeout):
        size=json.loads(req.data)['size'];calls.append(size)
        index=len(calls)
        clock[0]+=11 if fault=='slow' and index==3 else 1
        if fault=='transport' and index==3:raise URLError('test connection failed')
        value=response(size)
        if fault=='changed' and index==4:value['exceptions']=['changed explanation']
        raw=b'not json' if fault=='malformed' and index==3 else json.dumps(value).encode()
        class Reply:
            status=200
            def read(self):return raw
        yield Reply()
    # Save diagnostics separately: the validate callback consumes captured output.
    reports=[]
    def validate_after_print(value):
        reports.append(capsys.readouterr().out)
        assert 'HTTP' in reports[-1]
        if fault=='invalid' and len(calls)==3:raise AssertionError('test replay failure')
    monkeypatch.setattr(smoke,'urlopen',request)
    monkeypatch.setattr(smoke,'perf_counter',lambda:clock[0])
    monkeypatch.setattr(smoke,'validate_plan',validate_after_print)
    failures=smoke.run_smoke('http://test')
    output=''.join(reports)+capsys.readouterr().out
    assert calls==['fixture','fixture','full','full']
    assert failures and 'Planning HTTP smoke FAILED' in output
    assert 'full repeat: HTTP' in output
    assert 'full first:' in output
    if fault=='slow':assert 'HTTP 11.000s' in output and any('10-second' in f for f in failures)
    if fault in ('malformed','transport'):assert 'ERROR' in output
    if fault=='changed':assert 'MISMATCH' in output


def test_smoke_cli_failure_is_nonzero(monkeypatch):
    monkeypatch.setattr('sys.argv',['planning_smoke'])
    monkeypatch.setattr(smoke,'run_smoke',lambda url:['failed gate'])
    with pytest.raises(SystemExit) as error:smoke.main()
    assert error.value.code==1
