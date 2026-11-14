"""Report sparse gold coverage and graph integrity, not full semantic accuracy."""
import argparse
import json
from pathlib import Path
from backend.local_reasoning.schema import LocalResult,CaseInput
from backend.local_reasoning.validation import annotation_errors

ROOT=Path(__file__).resolve().parent


def main():
    p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,required=True);args=p.parse_args()
    before=json.loads((args.before/'predictions.json').read_text(encoding='utf-8'))
    after=json.loads((args.after/'predictions.json').read_text(encoding='utf-8'))
    assert [r['input'] for r in before]==[r['input'] for r in after], 'Inputs differ; no paired comparison'
    labels={r['id']:r for r in json.loads((ROOT/'fixtures/semantic_graph/user10_expected.json').read_text(encoding='utf-8'))['cases']}
    rows=[];actions_found=actions_total=relations_found=relations_total=0;errors=[]
    for old,row in zip(before,after):
        result=LocalResult.model_validate(row['local'])
        q=CaseInput(messages=[{'id':m['id'],'speaker_id':m['speaker'],'scope_id':'analysis','text':m['text']} for m in row['input']['messages']])
        issues=annotation_errors(q,result.annotations)
        if issues:errors.append({'id':row['id'],'errors':issues})
        actions={e.semantic.normalized_action for e in result.annotations.events if e.semantic}
        methods={r.rule_id for r in result.annotations.relations}
        want=labels[row['id']]
        af=set(want['actions'])&actions;rf=set(want['relations'])&methods
        actions_found+=len(af);actions_total+=len(want['actions']);relations_found+=len(rf);relations_total+=len(want['relations'])
        rows.append({'id':row['id'],'before':old['runs'][0]['response']['risk_status'],'after':row['runs'][0]['response']['risk_status'],
            'clauses':result.annotations.graph_trace.get('clauses'),
            'candidate_relations':len(result.annotations.graph_trace.get('candidates',[])),
            'kept_graph_relations':result.annotations.graph_trace.get('relations_kept'),
            'rejected':len(result.annotations.graph_trace.get('rejected',[])),
            'validation_removed':result.annotations.graph_trace.get('validation_removed_relations'),
            'missing_required_actions':sorted(set(want['actions'])-actions),'missing_required_relations':sorted(set(want['relations'])-methods)})
    summary={'rows':rows,'sparse_required_action_coverage':{'found':actions_found,'total':actions_total},
        'sparse_required_relation_coverage':{'found':relations_found,'total':relations_total},'structural_errors':errors,
        'scope':'Development sparse annotations, not exhaustive extraction precision, coreference accuracy, or independent quality.'}
    (args.after/'layer_review.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# Rà từng tầng trên 10 ca','','Đầu vào trước/sau giống nhau; nhãn sparse development, chưa chấm đầy đủ mọi sự kiện.','',
        '| Ca | Trước | Sau | Mệnh đề | Quan hệ ứng viên | Giữ | Loại |','|---|---|---|---:|---:|---:|---:|']
    for r in rows:lines.append(f"| {r['id']} | {r['before']} | {r['after']} | {r['clauses']} | {r['candidate_relations']} | {r['kept_graph_relations']} | {r['rejected']} |")
    (args.after/'LAYERS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k!='rows'},ensure_ascii=False))
    if errors or actions_found!=actions_total or relations_found!=relations_total:raise SystemExit(1)


if __name__=='__main__':main()
