"""Drop invalid evidence and all dependent annotations, keeping valid independent findings."""
from .validation import annotation_errors


def sanitize(input,annotations):
    if not annotation_errors(input,annotations):return annotations,[]
    a=annotations.model_copy(deep=True)
    messages={m.id:m.text for m in input.messages};contexts={c.id:c.text for c in input.context_facts}
    valid=[]
    for s in a.spans:
        text=messages.get(s.message_id) if s.context_id is None else contexts.get(s.context_id) if s.message_id is None else None
        if text is not None and 0<=s.start<s.end<=len(text) and text[s.start:s.end]==s.quote:valid.append(s)
    a.spans=valid;ids={s.span_id for s in valid};discarded=[e.event_id for e in a.events if not set(e.evidence_refs)<=ids]
    a.events=[e for e in a.events if e.event_id not in discarded];eids={e.event_id for e in a.events}
    people={p.participant_id for p in a.participants};entities=eids|people
    a.relations=[r for r in a.relations if r.from_id in entities and r.to_id in entities and set(r.evidence_refs)<=ids]
    event_map={e.event_id:e for e in a.events}
    a.relations=[r for r in a.relations if all(event_map[x].scope_id==r.scope_id for x in (r.from_id,r.to_id) if x in event_map)]
    rids={r.relation_id for r in a.relations}
    a.personal_relationships=[r for r in a.personal_relationships if set(r.evidence_refs)<=ids]
    for p in a.participants:p.evidence_refs=[x for x in p.evidence_refs if x in ids]
    for field in a.answers_18.__dict__.values():
        lost_dependency=not set(field.evidence_refs)<=ids or not set(field.value.event_ids)<=eids or not set(field.value.relation_ids)<=rids
        if lost_dependency:field.value.statements=[]
        field.evidence_refs=[x for x in field.evidence_refs if x in ids]
        field.value.event_ids=[x for x in field.value.event_ids if x in eids]
        field.value.relation_ids=[x for x in field.value.relation_ids if x in rids]
        if not field.evidence_refs:
            field.value.statements=[];field.status='unknown'
    if annotation_errors(input,a):raise ValueError('Annotations still invalid after dependency pruning')
    a.limitations.append('Đã loại chứng cứ không hợp lệ và kết luận phụ thuộc; kết quả phân tích một phần.')
    return a,discarded
