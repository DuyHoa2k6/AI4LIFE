"""Known development examples through the actual API; never independent accuracy."""
import hashlib
import json
import os
from pathlib import Path
import time
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.local_reasoning.schema import LocalResult
from backend.settings import get_setting

ROOT=Path(__file__).resolve().parent


def main():
    graph_enabled=get_setting('SCAMSHIELD_SEMANTIC_GRAPH_ENABLED','1')=='1'
    output=ROOT/('reports/clause_roles_graph_20261113' if graph_enabled else 'reports/clause_roles_20261113')
    output.mkdir(parents=True,exist_ok=True)
    fixture=ROOT/'fixtures/local_pipeline_20261113'
    names=['commission','alternate_account','refund_login_code','phone_handover_unpaid','invoice_account_change',
           'overseas_work_documents','login_code_warning','phone_payment_updated']
    records=[]
    with patch.dict(os.environ,{'SCAMSHIELD_MODE':'local_rules','SCAMSHIELD_REASONER':'legacy','SCAMSHIELD_CONTEXT_ENABLED':'1','SCAMSHIELD_URL_NETWORK_ENABLED':'0'}), \
         patch('httpx.AsyncClient.send',new_callable=AsyncMock,side_effect=AssertionError('External transport forbidden')) as network, TestClient(app) as client:
        for name in names:
            oldpath=ROOT/'reports/local_pipeline_20261113'/f'{name}_test.json'
            # Previous untouched predictions are the input source for the exact
            # examples already submitted by the user, not reference labels.
            old=json.loads(oldpath.read_text(encoding='utf-8')) if oldpath.exists() else None
            text=old['input']['text'] if old else (fixture/f'{name}.txt').read_text(encoding='utf-8').strip()
            started=time.perf_counter();response=client.post('/api/analyze',json={'text':text})
            elapsed=(time.perf_counter()-started)*1000
            raw=client.post('/api/analyze-local',json={'messages':[{'id':'m1','scope_id':'analysis','text':text}]})
            records.append({'id':name,'input':{'text':text},'http_status':response.status_code,'elapsed_ms':round(elapsed,3),
                'before':old['response']['risk_status'] if old else None,'response':response.json(),'local':raw.json()})
        transport_calls=network.call_count
    (output/'predictions.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    # Expectations are loaded only after predictions have been persisted.
    expected_path=ROOT/'fixtures'/('clause_roles_expected_graph.json' if graph_enabled else 'clause_roles_expected.json')
    expected=json.loads(expected_path.read_text(encoding='utf-8'))
    failed=[];lines=['# Kết quả kiểm thử cụm câu và vai trò','',
        'Tám ca người dùng đã cung cấp, dùng để phát triển; không phải tập độc lập. Luồng API thật, ASGI TestClient, URL network tắt, không gọi mô hình.','',
        '| Ca | Trước | Hiện tại | Kỳ vọng | API ms |','|---|---|---|---|---:|']
    for row in records:
        risk=row['response'].get('risk_status')
        if row['http_status']!=200 or risk!=expected[row['id']]:failed.append(row['id'])
        lines.append(f"| {row['id']} | {row['before']} | {risk} | {expected[row['id']]} | {row['elapsed_ms']} |")
        local=LocalResult.model_validate(row['local'])
        assert local.interpretation is not None
    lines+=['','## Nội dung và giải thích','']
    for row in records:
        lines += [f"### {row['id']}",'',row['input']['text'],'',row['response'].get('summary',''),'',
            'Hành động: '+' '.join(row['response'].get('recommended_actions',[])),'']
    timings=sorted(r['elapsed_ms'] for r in records)
    summary={'cases':len(records),'matched':len(records)-len(failed),'failed':failed,'external_transport_calls':transport_calls,
        'p50_ms':(timings[3]+timings[4])/2,'p95_ms':timings[-1],
        'measurement':'ASGI TestClient, sequential single request/case, no controlled cold start or browser measurement; development examples only.',
        'hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
            [ROOT/'backend/local_reasoning/clause_context.py',ROOT/'backend/local_reasoning/interpretation_schema.py',expected_path]}}
    (output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    (output/'CASES.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))
    if failed or transport_calls:raise SystemExit(1)


if __name__=='__main__':main()
