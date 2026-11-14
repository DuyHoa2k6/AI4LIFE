"""Rescore immutable saved predictions; never invokes inference or changes labels."""
import argparse,json
from pathlib import Path
from .io import load,jsonl,dump,digest
from .metrics import diagnose,aggregate

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);args=p.parse_args();folder=args.run
    manifest=json.loads((folder/'run_manifest.json').read_text());rows=[]
    for path,sha in manifest['datasets'].items():
        if digest(path)!=sha:raise ValueError('Reference dataset hash changed')
        rows+=load(path)
    predictions=[json.loads(x) for x in (folder/'predictions.jsonl').read_text(encoding='utf-8').splitlines()]
    diagnostics=[diagnose(r,p['prediction']) for r,p in zip(rows,predictions)]
    if [r.case_id for r in rows]!=[p['case_id'] for p in predictions]:raise ValueError('Prediction order/ID mismatch')
    metrics=json.loads((folder/'metrics.json').read_text());metrics['all']=aggregate(diagnostics)
    metrics['by_domain']={d:aggregate([r for r in diagnostics if r['domain']==d]) for d in metrics['by_domain']}
    metrics['by_split']={s:aggregate([r for r in diagnostics if r['split']==s]) for s in metrics['by_split']}
    for filename,key in [('oracle_predictions.jsonl','oracle_annotations'),('oracle_span_predictions.jsonl','oracle_model_spans')]:
        f=folder/filename
        if f.exists():
            ps=[json.loads(x) for x in f.read_text(encoding='utf-8').splitlines()]
            metrics[key]=aggregate([diagnose(r,p['prediction']) for r,p in zip(rows,ps)])
    metrics['scorer_sha256']=digest(Path(__file__).with_name('metrics.py'))
    jsonl(folder/'case_diagnostics.jsonl',diagnostics);jsonl(folder/'error_log.jsonl',[{'case_id':r.case_id,'model_version':manifest['model_version'],'dataset_version':manifest['dataset_version'],**e} for r,d in zip(rows,diagnostics) for e in d['errors']]);dump(folder/'metrics.json',metrics)

if __name__=='__main__':main()
