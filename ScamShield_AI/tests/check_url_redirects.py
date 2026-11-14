"""Public test endpoints only; --live additionally runs the configured Gemini pipeline."""
import argparse
import json
import time
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from backend.main import app
from backend.url_network import check_redirects

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true');args=parser.parse_args()
    output=Path('reports/url_redirects');output.mkdir(parents=True,exist_ok=True)
    rows=[]
    for url in ['https://httpbin.org/redirect/2','https://httpbin.org/status/404','http://127.0.0.1/private']:
        result=check_redirects(url)
        rows.append({'input':url,'network':result.model_dump()})
    (output/'live_network.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(rows))
    if args.live:
        payload={'text':'Tôi đang đọc tài liệu thử nghiệm chuyển hướng HTTP tại https://httpbin.org/redirect/2. Không có yêu cầu đăng nhập, giao mã hoặc chuyển tiền.'}
        (output/'live_input.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
        started=time.perf_counter()
        with TestClient(app) as client:r=client.post('/api/analyze',json=payload)
        result={'http_status':r.status_code,'seconds':time.perf_counter()-started,'response':r.json()}
        (output/'live_pipeline.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'http_status':r.status_code,'seconds':result['seconds'],'risk_status':r.json().get('risk_status'),'code':r.json().get('code')}))
