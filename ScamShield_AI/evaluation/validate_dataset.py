import argparse,json
from collections import Counter
from pathlib import Path
from .io import load,validate_splits,dump,digest
from .ontology import ERROR_TYPES
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--cases',type=Path,action='append',required=True);parser.add_argument('--out',type=Path);args=parser.parse_args()
    try:
        rows=[r for p in args.cases for r in load(p)];duplicates=validate_splits(rows)
        if len({r.case_id for r in rows})!=len(rows):raise ValueError('duplicate case IDs across files')
        report={'n':len(rows),'hashes':{str(p):digest(p) for p in args.cases},'review':dict(Counter(r.review_status for r in rows)),
          'seen':dict(Counter(r.novelty for r in rows)),'domain_risk':{d:{risk:sum(r.domain==d and r.expected.risk_status==risk for r in rows) for risk in ['clear','need_context','suspicious','high']} for d in sorted({r.domain for r in rows})},
          'phenomena_by_domain':{d:sorted({p for r in rows if r.domain==d for p in r.phenomena}) for d in sorted({r.domain for r in rows})},'near_duplicate_pairs':duplicates,
          'ambiguities':[r.case_id for r in rows if r.annotation_ambiguity],'independent_holdout':False,'accepted_error_types':ERROR_TYPES}
        if args.out:dump(args.out,report)
        print(json.dumps(report,ensure_ascii=False))
    except (ValueError,OSError) as exc:
        print(json.dumps({'valid':False,'reason':str(exc)},ensure_ascii=False));raise SystemExit(2)

if __name__=='__main__':main()
