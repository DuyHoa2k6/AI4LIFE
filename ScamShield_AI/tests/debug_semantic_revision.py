"""Explicit local exception diagnosis on synthetic public inputs, never production logs."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from backend.local_reasoning.engine import analyze_local
from backend.local_reasoning.schema import CaseInput
row=json.loads((ROOT/'fixtures/reasoning_document_20261114/inputs.jsonl').read_text(encoding='utf-8').splitlines()[int(sys.argv[1]) if len(sys.argv)>1 else 0])
def trace(frame,event,arg):
    if event=='exception' and isinstance(arg[1],ValueError) and frame.f_code.co_filename.endswith(('legacy_engine.py','semantic_contract.py','fact_validation.py')):
        print(frame.f_code.co_filename,frame.f_lineno,type(arg[1]).__name__,str(arg[1])[:1500])
        if frame.f_code.co_filename.endswith('fact_validation.py'):
            from backend.local_reasoning.validation import annotation_errors
            print(annotation_errors(frame.f_locals['input'],frame.f_locals['a']))
            a=frame.f_locals['a'];events={e.event_id:e for e in a.events}
            for r in a.relations:
                x,y=events.get(r.from_id),events.get(r.to_id)
                if x and y:print(r.type,x.event_type,x.affected_party_id,y.event_type,y.affected_party_id)
    return trace
sys.settrace(trace)
result=analyze_local(CaseInput(messages=[{'id':m['id'],'speaker_id':m['speaker'],'text':m['text'],'scope_id':'analysis'} for m in row['request']['messages']]))
sys.settrace(None);print(result.analysis_status,result.assessment.risk_status)
