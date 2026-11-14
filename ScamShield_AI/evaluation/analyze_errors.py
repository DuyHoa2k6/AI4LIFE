import argparse,json
from pathlib import Path
from collections import Counter
from .io import jsonl,dump

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    errors=[json.loads(x) for x in (args.run/'error_log.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
    grouped={}
    for e in errors:grouped.setdefault(e['case_id'],[]).append(e)
    args.out.mkdir(parents=True,exist_ok=True)
    jsonl(args.out/'review_queue.jsonl',[{'case_id':case,'error_types':sorted({e['error_type'] for e in es}),
      'state':'awaiting_human_review','reviewer_reference':[],'train_eligible':False,'notes':'Predictions are not reference labels. Confirm annotations and root causes independently.'} for case,es in grouped.items()])
    dump(args.out/'triage.json',{'n_error_cases':len(grouped),'errors':len(errors),'types':dict(Counter(e['error_type'] for e in errors)),
      'confirmed_structural':[e for e in errors if e['root_cause_status']=='confirmed'],'new_reviewed_training_samples':0})
    print(json.dumps({'cases':len(grouped),'errors':len(errors),'reviewed_training_samples':0}))

if __name__=='__main__':main()
