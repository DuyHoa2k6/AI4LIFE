"""Export reviewed cases only; no model weights are trained by this utility."""
import argparse
import hashlib
import json
from pathlib import Path
from backend.local_reasoning.schema import DatasetCase
from backend.local_reasoning.validation import dataset_errors
from backend.local_reasoning.splits import plan
from backend.local_reasoning.extract import DATA


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--dataset',type=Path);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();source=args.dataset or DATA/json.loads((DATA/'manifest.json').read_text(encoding='utf-8'))['canonical_pilot']
    cases=[DatasetCase.model_validate_json(s) for s in source.read_text(encoding='utf-8').splitlines() if s.strip()]
    errors=dataset_errors(cases)
    if errors:raise SystemExit('Invalid dataset: '+','.join(errors))
    result=plan(cases);args.output.mkdir(parents=True,exist_ok=False)
    for split in ('train','dev','test'):
        selected=[c for c in cases if result['assignments'].get(c.metadata.case_id)==split]
        for c in selected:c.metadata.split=split
        (args.output/(split+'.jsonl')).write_text('\n'.join(c.model_dump_json() for c in selected)+ ('\n' if selected else ''),encoding='utf-8')
    status={'status':'ready_for_supervised_training' if result['assignments'] else 'not_ready_no_reviewed_cases',
            'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'plan':result,
            'model_trained':False,'note':'Independent evaluation data must remain outside this process; never auto-promote weak labels.'}
    (args.output/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':status['status'],'exported':len(result['assignments']),'model_trained':False}))
