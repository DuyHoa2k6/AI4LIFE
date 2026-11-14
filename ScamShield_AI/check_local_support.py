"""Export real local API responses; optional support observations are explicit test fixtures."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from time import perf_counter
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app
from backend import retrieval
from backend.schemas import UrlNetworkCheck, RedirectHop


def run(output):
    output.mkdir(parents=True,exist_ok=False)
    cases=[('url_request','Đăng nhập tại https://youtubee.com/'),
           ('url_warning','Cảnh báo: đừng đăng nhập tại https://youtubee.com/'),
           ('url_only','https://youtubee.com/'),
           ('ordinary_domain','Đăng nhập tại https://youtube.com/'),
           ('high_text','Gửi mã OTP cho tôi tại https://youtubee.com/'),
           ('separate_context','Đăng nhập tại đây. Ví dụ tên miền: https://youtubee.com/'),
           ('urgent','Hiện tại tôi bị giữ lại và không được rời đi.')]
    rows=[]
    def record(cid,text,fixture='none; actual production index; URL network disabled'):
        start=perf_counter();r=TestClient(app).post('/api/analyze',json={'text':text})
        rows.append({'id':cid,'input':{'text':text},'support_fixture':fixture,
                     'http_status':r.status_code,'testclient_ms':(perf_counter()-start)*1000,'response':r.json()})
    with patch.dict(os.environ,{'SCAMSHIELD_MODE':'local_rules','SCAMSHIELD_URL_NETWORK_ENABLED':'0',
                                'SCAMSHIELD_RAG_ENABLED':'1'}):
        for cid,text in cases:record(cid,text)
        synthetic=dict(id='TEST-ONLY',source_url='https://test.gov.vn/fixture',
            text='Không gửi mã OTP hoặc mật khẩu cho người khác.',actions=['provide_code','share_auth_code'],
            review_status='approved',reviewer='SYNTHETIC FIXTURE ONLY',reuse_approved=True,
            approved_at='2020-01-01',checked_at='2020-01-01',valid_until='2099-01-01',source_role='behavior_support')
        with patch.object(retrieval,'read_records',return_value=[synthetic]):
            record('approved_fixture','Gửi mã OTP cho tôi.','synthetic approved record; NOT a real approved source')
        synthetic['review_status']='candidate'
        with patch.object(retrieval,'read_records',return_value=[synthetic]):
            record('candidate_fixture','Gửi mã OTP cho tôi.','synthetic candidate record')
        observed=UrlNetworkCheck(status='checked',hops=[
            RedirectHop(display_url='https://example.com/',http_status=302),
            RedirectHop(display_url='https://youtubee.com/',http_status=200)],
            final_url='https://youtubee.com/',final_hostname='youtubee.com',final_registered_domain='youtubee.com',
            final_http_status=200,reachable=True)
        with patch.dict(os.environ,{'SCAMSHIELD_URL_NETWORK_ENABLED':'1'}),patch('backend.url_network.check_redirects',return_value=observed):
            record('redirect_fixture','Đăng nhập tại https://example.com/','synthetic redirect observation; no website contacted')
    (output/'predictions.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Local text + RAG + URL: development examples','',
           'TestClient end-to-end API. No external model; redirects and approved sources explicitly simulated where noted.',
           'Not independent quality, browser latency, real source approval or real-domain reputation.','',
           '| Case | Input | Risk | Used sources | Used URLs | Support fixture |',
           '|---|---|---|---:|---:|---|']
    for row in rows:
        d=row['response'];lines.append(f"| {row['id']} | {row['input']['text']} | {d.get('risk_status',d.get('code'))} | {len(d.get('source_matches',[]))} | {len(d.get('url_uses',[]))} | {row['support_fixture']} |")
    (output/'CASES.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    base=Path(__file__).resolve().parent
    files=[base/'backend'/p for p in ['main.py','retrieval.py','url_network.py','urls.py','local_reasoning/support.py',
        'local_reasoning/engine.py','local_reasoning/adapter.py','local_reasoning/schema.py']]
    files += [base/'extension/result_view.js',base/'knowledge/url/domain_references.json',
              base.parent/'data/knowledge_sources.jsonl',base.parent/'data/v2/rulebook.json',
              base.parent/'data/v2/fact_rules.json',base.parent/'data/v2/fact_templates.json',base.parent/'data/v2/fact_catalog.json']
    (output/'hashes.json').write_text(json.dumps({os.path.relpath(p,base):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'cases':len(rows),'http_200':sum(r['http_status']==200 for r in rows),'output':str(output)}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    run(parser.parse_args().output)
