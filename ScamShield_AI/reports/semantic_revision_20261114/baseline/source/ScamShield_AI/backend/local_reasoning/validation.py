"""Structural/evidence validation; business truth still needs independent review."""
from collections import Counter
import json
import re
import unicodedata
from .schema import DatasetCase


def annotation_errors(input,a):
    errors=[]
    def unique(items,key,label):
        values=[getattr(x,key) for x in items]
        if len(values)!=len(set(values)):errors.append('duplicate_'+label)
    unique(a.spans,'span_id','span');unique(a.events,'event_id','event')
    unique(a.participants,'participant_id','participant');unique(a.relations,'relation_id','relation')
    unique(a.mentions,'mention_id','mention')
    messages={m.id:m for m in input.messages};contexts={c.id:c for c in input.context_facts}
    spans={s.span_id:s for s in a.spans};people={p.participant_id for p in a.participants};events={e.event_id:e for e in a.events}
    entities=people|events.keys()
    mentions={m.mention_id for m in a.mentions}
    for mention in a.mentions:
        if not set(mention.evidence_refs)<=spans.keys():errors.append('invalid_mention_evidence')
        if mention.participant_id is not None and mention.participant_id not in people:errors.append('invalid_mention_participant')
        if not set(mention.candidate_ids)<=people|mentions:errors.append('invalid_mention_candidates')
    for s in a.spans:
        text=messages[s.message_id].text if s.message_id in messages and s.context_id is None else contexts[s.context_id].text if s.context_id in contexts and s.message_id is None else None
        if text is None or not 0<=s.start<s.end<=len(text) or text[s.start:s.end]!=s.quote:errors.append('invalid_quote_offset')
    for p in a.participants:
        if not set(p.evidence_refs)<=spans.keys():errors.append('invalid_participant_evidence')
    for e in a.events:
        if not set(e.evidence_refs)<=spans.keys():errors.append('invalid_event_evidence');continue
        if any(x is not None and x not in people for x in (e.actor_id,e.recipient_id,e.affected_party_id)):errors.append('invalid_event_participant')
        if e.attribution.speaker_id is not None and e.attribution.speaker_id not in {m.speaker_id for m in input.messages}:errors.append('invalid_attribution')
        if e.speech_role in ('quoted_warning','hypothetical') and e.attribution.kind not in ('quoted_warning','hypothetical'):errors.append('inconsistent_attribution')
        if not e.scope_id:errors.append('event_missing_scope')
        if e.semantic:
            v=e.semantic
            if v.situation_id!=e.scope_id:errors.append('semantic_scope_mismatch')
            if v.message_id is not None and v.message_id not in messages or v.context_id is not None and v.context_id not in contexts:errors.append('semantic_source_missing')
            if any(p is not None and p not in people for p in (v.speaker_id,v.requester_id,v.performer_id,v.affected_party_id)):errors.append('semantic_participant_missing')
            if not set(v.negation_scope_refs)<=spans.keys():errors.append('semantic_negation_span_missing')
            if not set(v.mention_refs)<=mentions:errors.append('semantic_mention_missing')
            if not set(v.consequence_refs)<=events.keys():errors.append('semantic_consequence_missing')
            if v.condition and not set(v.condition.get('evidence_refs',[]))<=spans.keys():errors.append('semantic_condition_evidence_missing')
    for r in a.relations:
        if r.from_id not in entities or r.to_id not in entities or not set(r.evidence_refs)<=spans.keys():errors.append('invalid_relation_reference');continue
        endpoints=[events[x] for x in (r.from_id,r.to_id) if x in events]
        if any(e.scope_id!=r.scope_id for e in endpoints):errors.append('cross_scope_relation')
        if not all(set(e.evidence_refs)&set(r.evidence_refs) for e in endpoints):errors.append('relation_missing_endpoint_evidence')
        if len(endpoints)==2 and endpoints[0].affected_party_id and endpoints[1].affected_party_id and endpoints[0].affected_party_id!=endpoints[1].affected_party_id:errors.append('cross_person_relation')
    for relation in a.personal_relationships:
        if not set(relation.participant_ids)<=people or not set(relation.evidence_refs)<=spans.keys():errors.append('invalid_personal_relationship')
    rids={r.relation_id for r in a.relations}
    for f in a.answers_18.__dict__.values():
        if not set(f.evidence_refs)<=spans.keys() or not set(f.value.event_ids)<=events.keys() or not set(f.value.relation_ids)<=rids or not set(f.value.participant_ids)<=people:errors.append('invalid_answer_reference')
    return sorted(set(errors))


def dataset_errors(cases):
    errors=[];ids=set();groups={};texts={}
    for case in cases:
        m=case.metadata
        if m.case_id in ids:errors.append('duplicate_case_id')
        ids.add(m.case_id)
        if m.review_status=='reviewed' and len(set(m.reviewers))<2:errors.append('reviewed_without_two_reviewers')
        for label,key in (('scenario',m.scenario_id),('variant',m.variant_group_id),('source',m.source_group_id)):
            if key:
                previous=groups.setdefault((label,key),m.split)
                if previous!=m.split:errors.append('cross_split_'+label)
        # Source type, parent links and supplied context can change interpretation;
        # OCR under a warning and an independent comment are legitimate controls.
        effective=case.input.model_dump(mode='json',exclude={'user_question'})
        for message in effective['messages']:message['text']=' '.join(unicodedata.normalize('NFC',message['text']).casefold().split())
        for fact in effective['context_facts']:fact['text']=' '.join(unicodedata.normalize('NFC',fact['text']).casefold().split())
        normalized=json.dumps(effective,sort_keys=True,ensure_ascii=False)
        if normalized in texts:errors.append('normalized_exact_duplicate')
        texts[normalized]=m.case_id
        errors.extend(annotation_errors(case.input,case.annotations))
        assessment=case.expected_assessment
        if assessment:
            span_ids={s.span_id for s in case.annotations.spans}
            if not set(assessment.evidence_refs+assessment.urgency_evidence_refs)<=span_ids:errors.append('invalid_assessment_evidence')
            if assessment.safety_urgency=='urgent' and not assessment.urgency_evidence_refs:errors.append('urgent_without_evidence')
            if assessment.risk_status in ('suspicious','high') and (not assessment.evidence_refs or not assessment.applicable_rule_ids):errors.append('conclusion_without_rule_evidence')
    return sorted(set(errors))
