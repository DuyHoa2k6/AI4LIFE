"""Same-request API measurement. No reference labels are opened until scoring."""
import argparse,json,sys,time,hashlib,shutil,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run_reasoning_document import rows,jsonl,dump,sha
from backend.diagnostics import capture_traces
from backend.main import app
from backend.settings import get_setting
from fastapi.testclient import TestClient

def run(out,freeze=False):
    if (out/'predictions.jsonl').exists():raise ValueError('Do not overwrite predictions')
    out.mkdir(parents=True,exist_ok=True)
    cases=rows(ROOT/'fixtures/reasoning_document_20261114/inputs.jsonl')
    sources=[p for p in (ROOT/'backend').rglob('*.py') if p.name!='local_settings.py']+list((ROOT.parent/'data/v2').rglob('*.json'))
    hashes={str(p.relative_to(ROOT.parent)):sha(p) for p in sources}
    if freeze:
        for p in sources:
            dst=out/'source'/p.relative_to(ROOT.parent);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
    manifest={'mode':get_setting('SCAMSHIELD_MODE','local_rules'),'reasoner':get_setting('SCAMSHIELD_REASONER','legacy'),'model_version':None,'tokenizer_version':'local-unicode-normalization-not-PhoBERT','schema_version':'2.0-public/local-2.0','dataset_version':'public-16-20261114','input_hash':sha(ROOT/'fixtures/reasoning_document_20261114/inputs.jsonl'),'source_hashes':hashes,'same_request_trace':True,'reference_opened_during_prediction':False}
    predictions=[];traces=[]
    with TestClient(app) as client:
        for case in cases:
            start=time.perf_counter()
            with capture_traces() as records:response=client.post('/api/analyze',json=case['request'])
            elapsed=(time.perf_counter()-start)*1000;body=response.json()
            predictions.append({'case_id':case['case_id'],'elapsed_ms':elapsed,'http_status':response.status_code,'response':body})
            if len(records)!=1 or records[0]['request_id']!=body.get('request_id'):
                dump(out/'failed_request.json',{'case_id':case['case_id'],'http_status':response.status_code,'response':body,'trace_count':len(records)})
                raise ValueError('Same-request trace binding failed; see failed_request.json')
            traces.append({'case_id':case['case_id'],**records[0]});jsonl(out/'predictions.jsonl',predictions);jsonl(out/'traces.jsonl',traces)
            print(case['case_id'],response.status_code,body.get('risk_status'),round(elapsed,2),flush=True)
    manifest['prediction_sha256_before_score']=sha(out/'predictions.jsonl');manifest['rule_version']=traces[0]['versions'];dump(out/'manifest.json',manifest)
    expected={r['case_id']:r['risk_status'] for r in rows(ROOT/'fixtures/reasoning_document_20261114/reference_draft.jsonl')}
    metrics={'public_draft_only':True,'n':len(predictions),'level_matches':sum(r['response'].get('risk_status')==expected[r['case_id']] for r in predictions),'cases':[{ 'case_id':r['case_id'],'expected_draft':expected[r['case_id']],'actual':r['response'].get('risk_status'),'analysis_status':r['response'].get('analysis_status'),'ms':r['elapsed_ms']} for r in predictions]}
    times=sorted(r['elapsed_ms'] for r in predictions);metrics['p50_ms']=times[math.ceil(len(times)*.5)-1];metrics['p95_ms']=times[math.ceil(len(times)*.95)-1];dump(out/'metrics.json',metrics)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--freeze',action='store_true');args=p.parse_args();run(args.out,args.freeze)
