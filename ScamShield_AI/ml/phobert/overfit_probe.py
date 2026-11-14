"""Resubstitution diagnostic only; never included in validation/independent scores."""
import json
from pathlib import Path
from .data import load
from .schema import runtime_input
from .inference import Runtime
from .evaluate import score
ROOT=Path(__file__).resolve().parents[2]

def main():
    runtime=Runtime(ROOT/'artifacts/phobert/overfit_heads',allow_experimental=True)
    ids=set(runtime.manifest['data']['train']['selected_ids'])
    rows=[r for r in load(ROOT/runtime.config['train']) if r.id in ids]
    outputs=[runtime.predict(runtime_input(r)) for r in rows]
    out=ROOT/'reports/phobert_20261114'
    (out/'overfit_predictions.json').write_text(json.dumps([{'id':r.id,'input':runtime_input(r),'prediction':p} for r,p in zip(rows,outputs)],ensure_ascii=False,indent=2),encoding='utf-8')
    metrics=score(rows,outputs)
    (out/'overfit_report.json').write_text(json.dumps({'scope':'same four training samples; resubstitution, not independent accuracy','n':len(rows),'metrics':metrics},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'n':len(rows),'span_action':metrics['spans']['action'],'risk_macro_f1':metrics['risk']['macro_f1']}))

if __name__=='__main__':main()
