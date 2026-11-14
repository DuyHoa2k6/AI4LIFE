import argparse,json
from pathlib import Path
from .io import load,dump

def main():
    p=argparse.ArgumentParser();p.add_argument('--cases',type=Path,required=True);p.add_argument('--run',type=Path,required=True);args=p.parse_args()
    cases=load(args.cases);by_id={r.case_id:r for r in cases};pred={r['case_id']:r['prediction'] for r in [json.loads(x) for x in (args.run/'predictions.jsonl').read_text(encoding='utf-8').splitlines()]};records=[]
    for r in cases:
        if not r.metamorphic_parent:continue
        parent=by_id[r.metamorphic_parent];a=pred[parent.case_id]['assessment'].get('risk_status');b=pred[r.case_id]['assessment'].get('risk_status')
        records.append({'parent':parent.case_id,'child':r.case_id,'transformation':r.metamorphic_relation,
          'phenomena':r.phenomena,'expected_parent':parent.expected.risk_status,'expected_child':r.expected.risk_status,'predicted_parent':a,'predicted_child':b,
          'risk_invariant':a==b if r.metamorphic_relation=='same_meaning' else None,
          'both_match_draft':a==parent.expected.risk_status and b==r.expected.risk_status,'independent':False,'ambiguous':bool(r.annotation_ambiguity)})
    dump(args.run/'metamorphic.json',{'n':len(records),'cases':records,'note':'Invariance is separate from correctness; same wrong label on both is not semantic success.'})
    print(json.dumps({'pairs':len(records),'both_match_draft':sum(r['both_match_draft'] for r in records)}))

if __name__=='__main__':main()
