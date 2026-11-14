"""Local human review packs. No model calls, auto-approval or pseudo-labelling."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Literal
from pydantic import Field
from ml.phobert.schema import Strict,Span,RISKS
from .schema import Case,Expected
from .ontology import POLICY_ATTRS
from .io import load,dump,jsonl,digest

TASKS=('spans','events','roles','relations','risk','explanation','questions')

class Annotation(Strict):
    case_id:str
    input_sha256:str=Field(pattern=r'^[a-f0-9]{64}$')
    expected:Expected|None
    partial_annotations:dict=Field(default_factory=dict)
    annotation_completeness:dict[str,Literal['complete','partial','unannotated']]
    issues:list[str]=[]

class Attestation(Strict):
    reviewer_reference:str=Field(min_length=3,max_length=200)
    human_review_performed:bool
    independent_of_other_reviewer:bool
    used_model_generated_annotations:bool

class Resolution(Annotation):
    adjudicator_reference:str=Field(min_length=3,max_length=200)
    human_resolution_performed:bool
    approved_for_training:bool
    reason:str=Field(min_length=5)

def input_digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()

def identifier(value):return hashlib.sha256(value.encode('utf-8')).hexdigest()

def read_pack(directory):
    manifest=json.loads((directory/'pack_manifest.json').read_text(encoding='utf-8'))
    for filename,sha in manifest['files'].items():
        # Never accept paths supplied through a modified manifest outside the pack.
        file=(directory/filename).resolve()
        if not file.is_relative_to(directory.resolve()) or digest(file)!=sha:raise ValueError('Review pack file/hash changed')
    rows=[json.loads(x) for x in (directory/'inputs.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
    return manifest,{r['case_id']:r for r in rows}

def export_pack(source,out,case_ids=None):
    if (out/'pack_manifest.json').exists():raise ValueError('Review pack already exists; do not overwrite an active review')
    rows=load(source)
    if case_ids:
        if set(case_ids)-{r.case_id for r in rows}:raise ValueError('Unknown selected case ID')
        rows=[r for r in rows if r.case_id in case_ids]
    if not rows:raise ValueError('No cases selected')
    if any(r.split=='locked' for r in rows):raise ValueError('Use independent custodian workflow for locked evaluation data')
    inputs=[{'case_id':r.case_id,'domain':r.domain,'input':r.input.model_dump(),'input_sha256':input_digest(r.input.model_dump())} for r in rows]
    out.mkdir(parents=True,exist_ok=True)
    jsonl(out/'inputs.jsonl',inputs)
    jsonl(out/'annotations_blank.jsonl',[{'case_id':r['case_id'],'input_sha256':r['input_sha256'],'expected':None,'partial_annotations':{},'annotation_completeness':{t:'unannotated' for t in TASKS},'issues':[]} for r in inputs])
    dump(out/'expected.schema.json',Expected.model_json_schema())
    dump(out/'ontology.json',{'version':'eval-ontology-1.0','attributes':POLICY_ATTRS})
    (out/'INSTRUCTIONS.md').write_text('''# Gói rà soát đầu vào

Chỉ có nội dung gốc và định nghĩa schema; không có nhãn draft hoặc dự đoán của model.
Family/template/source group bị loại vì một số ID cũ chứa tên mức cảnh báo.
Đây vẫn là dữ liệu công khai đã được agent xem, không phải blind holdout.

Mỗi người rà nhận bản sao gói này, tự sao chép annotations_blank.jsonl sang file
riêng rồi điền expected và độ hoàn thiện từng task. Không sửa inputs.jsonl hoặc
file gốc trong pack. Không xem kết quả của người rà kia trong lượt độc lập.

Đọc evaluation/annotation_guide.md. Offset là Unicode code point, end loại trừ.
Chưa gán nhãn khác với không có hành vi. Không đoán danh tính hoặc tội danh.
Reference người rà nên là mã công việc không nhận dạng cá nhân, không cần tên thật.

CLI submit cần attestation có reviewer_reference thực, human_review_performed=true,
independent_of_other_reviewer=true, used_model_generated_annotations=false. Phần mềm
chỉ ghi nhận lời xác nhận, không thể tự chứng minh con người đã rà độc lập.

Hai bản gán nhãn chỉ tạo báo cáo đồng thuận/bất đồng. Chúng không tự được đưa vào
train. Người chịu trách nhiệm phải lập resolution, ghi lý do, xác nhận đã rà và
chọn approved_for_training. Split, family và label mapping vẫn qua training gate.
''',encoding='utf-8')
    files={name:digest(out/name) for name in ['inputs.jsonl','annotations_blank.jsonl','expected.schema.json','ontology.json','INSTRUCTIONS.md']}
    manifest={'version':'review-pack-1.0','n':len(rows),'source_sha256':digest(source),'files':files,'source_label_status':'draft/public; not blind holdout',
      'case_input_hashes':{r['case_id']:r['input_sha256'] for r in inputs},'reviewed_count':0,'auto_training':False}
    dump(out/'pack_manifest.json',manifest);return manifest

def checked_annotation(source_case,value):
    if value.expected is None:raise ValueError('Blank annotation cannot count as human review')
    if set(value.annotation_completeness)!=set(TASKS):raise ValueError('Annotation task completeness is missing')
    if value.annotation_completeness['events']=='complete' and any(v is None for e in value.expected.events for v in e.attributes.values()):raise ValueError('Complete event attributes cannot contain unannotated null')
    original=source_case.model_dump();original.update(expected=value.expected.model_dump(),annotation_completeness=value.annotation_completeness,review_status='draft',reviewer_reference=[])
    return Case.model_validate(original)

def check_partial(source_case,value):
    if not value.partial_annotations:raise ValueError('Blank worksheet is not a review')
    if set(value.annotation_completeness)!=set(TASKS):raise ValueError('Annotation task completeness is missing')
    if not set(value.partial_annotations)<=set(Expected.model_fields):raise ValueError('Unknown partial annotation field')
    texts={m.id:m.text for m in source_case.input.messages};seen=set()
    for raw in value.partial_annotations.get('spans',[]):
        span=Span.model_validate(raw)
        if span.id in seen or span.message_id not in texts or not 0<=span.start<span.end<=len(texts[span.message_id]) or texts[span.message_id][span.start:span.end]!=span.quote:raise ValueError('Invalid partial span/offset')
        seen.add(span.id)
    if value.partial_annotations.get('risk_status') is not None and value.partial_annotations['risk_status'] not in RISKS:raise ValueError('Invalid partial risk label')

def submit(pack,source,annotation_file,attestation_file):
    manifest,inputs=read_pack(pack)
    if digest(source)!=manifest['source_sha256']:raise ValueError('Source dataset changed after exporting review pack')
    source_cases={r.case_id:r for r in load(source)}
    attestation=Attestation.model_validate_json(attestation_file.read_text(encoding='utf-8'))
    ref=attestation.reviewer_reference.strip()
    if ref.startswith('<') or ref.upper().startswith(('PENDING','EXAMPLE')):raise ValueError('A real project reviewer reference is required')
    if not ref or not attestation.human_review_performed or not attestation.independent_of_other_reviewer or attestation.used_model_generated_annotations:
        raise ValueError('Independent human annotation attestation is not satisfied')
    records=[Annotation.model_validate_json(x) for x in annotation_file.read_text(encoding='utf-8').splitlines() if x.strip()]
    if not records or len({r.case_id for r in records})!=len(records):raise ValueError('Empty submission or duplicate case IDs')
    pending=[]
    for row in records:
        if row.case_id not in inputs or row.input_sha256!=inputs[row.case_id]['input_sha256']:raise ValueError('Annotation does not match original case input')
        if row.expected is None:check_partial(source_cases[row.case_id],row)
        else:checked_annotation(source_cases[row.case_id],row)
        target=pack/'submissions'/identifier(ref)/(identifier(row.case_id)+'.json')
        if target.exists():raise ValueError('This reviewer already submitted this case; use an explicit new review cycle')
        record={'case_id':row.case_id,'input_sha256':row.input_sha256,'reviewer_reference':ref,'attestation':attestation.model_dump(),
          'annotation':row.model_dump(),'annotation_file_sha256':digest(annotation_file),'state':'partial_not_approved' if row.expected is None else 'submitted_not_approved'}
        record['record_sha256']=input_digest(record)
        pending.append((target,record))
    for path,record in pending:dump(path,record)
    return {'reviewer_reference':ref,'submitted':len(pending),'approved':0,'training_started':False}

def canonical(case):
    """Compare graph structure independently of ID names or explanatory wording."""
    e=case.expected;spans={s.id:(s.message_id,s.start,s.end,s.label) for s in e.spans}
    events={v.id:(spans[v.anchor_id],tuple(sorted(v.attributes.items())),v.information_status,tuple(sorted(spans[x] for x in v.argument_refs))) for v in e.events}
    key=lambda value:json.dumps(value,ensure_ascii=False,sort_keys=True)
    scopes={s.id:tuple(sorted((events[x] for x in s.event_refs),key=key)) for s in e.cases}
    participants={}
    for p in e.participants:
        if p.kind=='metadata':participants[p.id]=('metadata',p.speaker_id)
        elif p.kind=='mention':participants[p.id]=('mention',spans[p.span_id])
        else:participants[p.id]=('unresolved',tuple(sorted(((events[a.event_id],a.role) for a in e.event_arguments if a.participant_id==p.id),key=key)))
    rels=[]
    for r in e.relations:
        a,b=events[r.source_id],events[r.target_id]
        if r.type=='same_transaction':a,b=sorted([a,b],key=key)
        rels.append((a,b,r.type,scopes.get(r.scope_id),tuple(sorted(spans[x] for x in r.evidence_refs))))
    return {'spans':sorted(spans.values()),'events':sorted(((v,scopes.get(next(x.transaction_id for x in e.events if x.id==k))) for k,v in events.items()),key=key),
      'roles':sorted(((events[a.event_id],a.role,participants[a.participant_id]) for a in e.event_arguments),key=key),'relations':sorted(rels,key=key),
      'risk':e.risk_status,'decisive_events':sorted((events[x] for x in e.decisive_event_refs),key=key),'mechanisms':sorted(e.mechanism_tags),'missing':sorted(e.missing_information),'question_targets':sorted(e.acceptable_question_targets),
      'completeness':case.annotation_completeness}

def reviews_for(pack,case_id):
    values=[]
    for path in (pack/'submissions').glob('*/'+identifier(case_id)+'.json'):
        record=json.loads(path.read_text(encoding='utf-8'));record_hash=record.pop('record_sha256',None)
        if record_hash!=input_digest(record):raise ValueError('Submitted review record/hash changed')
        attestation=Attestation.model_validate(record['attestation'])
        if record['case_id']!=case_id or record['reviewer_reference']!=attestation.reviewer_reference.strip() or path.parent.name!=identifier(record['reviewer_reference']):raise ValueError('Review identity/case binding mismatch')
        if not attestation.human_review_performed or not attestation.independent_of_other_reviewer or attestation.used_model_generated_annotations:raise ValueError('Submitted human attestation is no longer valid')
        record['record_sha256']=record_hash;values.append(record)
    return values

def reconcile(pack,source,out):
    manifest,inputs=read_pack(pack)
    if digest(source)!=manifest['source_sha256']:raise ValueError('Source dataset changed')
    source_cases={r.case_id:r for r in load(source)};rows=[]
    for case_id,input_row in inputs.items():
        submissions=reviews_for(pack,case_id)
        if len(submissions)<2:rows.append({'case_id':case_id,'state':'needs_two_independent_reviews','reviews':len(submissions),'approved':False});continue
        if any(r['annotation']['expected'] is None for r in submissions):rows.append({'case_id':case_id,'state':'partial_annotation_needs_completion','reviews':len(submissions),'approved':False});continue
        canonical_values=[canonical(checked_annotation(source_cases[case_id],Annotation.model_validate(r['annotation']))) for r in submissions]
        fields=sorted({key for key in canonical_values[0] if any(value[key]!=canonical_values[0][key] for value in canonical_values[1:])})
        rows.append({'case_id':case_id,'state':'structural_disagreement' if fields else 'structural_agreement_pending_human_resolution',
          'reviewer_references':[r['reviewer_reference'] for r in submissions],'different_fields':fields,'approved':False,
          'free_text_semantic_review':'human_required; prose is not compared for exact wording'})
    jsonl(out,rows);return rows

def approve(pack,source,resolutions_file,out):
    manifest,inputs=read_pack(pack)
    if digest(source)!=manifest['source_sha256']:raise ValueError('Source dataset changed')
    if out.exists():raise ValueError('Reviewed export already exists; do not overwrite a version')
    source_cases={r.case_id:r for r in load(source)}
    resolutions=[Resolution.model_validate_json(x) for x in resolutions_file.read_text(encoding='utf-8').splitlines() if x.strip()]
    if not resolutions or len({r.case_id for r in resolutions})!=len(resolutions):raise ValueError('Empty resolutions or duplicate case IDs')
    approved=[];audit=[]
    for resolution in resolutions:
        if resolution.case_id not in inputs or resolution.input_sha256!=inputs[resolution.case_id]['input_sha256']:raise ValueError('Resolution input does not match pack')
        refs=reviews_for(pack,resolution.case_id)
        reviewers=sorted({r['reviewer_reference'] for r in refs})
        if len(reviewers)<2:raise ValueError('Two independent submitted reviews are required before approval')
        if any(r['annotation']['expected'] is None for r in refs):raise ValueError('Partial reviews require completion before a fully reviewed export')
        if not resolution.human_resolution_performed or not resolution.approved_for_training or resolution.issues:
            raise ValueError('Human resolution/approval is incomplete or still has unresolved issues')
        ref=resolution.adjudicator_reference.strip()
        if not ref or ref.startswith('<') or ref.upper().startswith(('PENDING','EXAMPLE')):raise ValueError('Actual human resolution reference is required')
        checked=checked_annotation(source_cases[resolution.case_id],resolution)
        comparisons=[canonical(checked_annotation(source_cases[resolution.case_id],Annotation.model_validate(r['annotation']))) for r in refs]
        disagreement=any(v!=comparisons[0] for v in comparisons[1:])
        data=checked.model_dump();data.update(review_status='adjudicated' if disagreement else 'human_verified',reviewer_reference=reviewers,annotation_ambiguity=[])
        data['provenance']['review_pack_source_sha256']=manifest['source_sha256']
        result=Case.model_validate(data);approved.append(result.model_dump())
        audit.append({'case_id':resolution.case_id,'reviewer_references':reviewers,'adjudicator_reference':resolution.adjudicator_reference,
          'resolution_reason':resolution.reason,'input_sha256':resolution.input_sha256,'review_record_hashes':[input_digest(r) for r in refs],
          'original_split':result.split,'family_promotion_required':result.split in ('validation','locked'),'blind_holdout':False})
    jsonl(out,approved)
    dump(out.with_suffix('.review_manifest.json'),{'version':'review-export-1.0','n':len(approved),'sha256':digest(out),'records':audit,
      'human_attestation':'recorded, not automatically proven','training_started':False,'source_file_unchanged_sha256':manifest['source_sha256']})
    return {'exported':len(approved),'training_started':False,'review_manifest':str(out.with_suffix('.review_manifest.json'))}

def main():
    p=argparse.ArgumentParser();subs=p.add_subparsers(dest='command',required=True)
    q=subs.add_parser('export');q.add_argument('--source',type=Path,required=True);q.add_argument('--out',type=Path,required=True);q.add_argument('--case-id',action='append')
    for cmd in ['submit','reconcile','approve']:
        q=subs.add_parser(cmd);q.add_argument('--pack',type=Path,required=True);q.add_argument('--source',type=Path,required=True)
        if cmd=='submit':q.add_argument('--annotations',type=Path,required=True);q.add_argument('--attestation',type=Path,required=True)
        else:q.add_argument('--out',type=Path,required=True)
        if cmd=='approve':q.add_argument('--resolutions',type=Path,required=True)
    args=p.parse_args()
    try:
        if args.command=='export':result=export_pack(args.source,args.out,args.case_id)
        elif args.command=='submit':result=submit(args.pack,args.source,args.annotations,args.attestation)
        elif args.command=='reconcile':
            result=reconcile(args.pack,args.source,args.out);result={'cases':len(result),'approved':0,'states':{s:sum(r['state']==s for r in result) for s in {r['state'] for r in result}}}
        else:result=approve(args.pack,args.source,args.resolutions,args.out)
        print(json.dumps(result,ensure_ascii=False))
    except (ValueError,OSError) as exc:print(json.dumps({'error':str(exc)},ensure_ascii=False));raise SystemExit(2)

if __name__=='__main__':main()
