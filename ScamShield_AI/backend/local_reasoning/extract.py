"""Adapt verified local observations and extract bounded human-safety facts."""
import json
from pathlib import Path
import re
from ..local_observation.analyzer import analyze as observe
from ..local_observation.text import normalize, quote_ranges
from ..local_observation.segmentation import segments
from ..local_observation.syntax import transaction_at
from ..local_observation.schema import Answers18, AnalysisField, Value
from .schema import Annotations, Participant, Span, Event, Relation, Attribution, PersonalRelationship
from .rule_schema import ExtractionRules

DATA=Path(__file__).resolve().parents[3]/'data/v2'


def base(input):
    people=[];seen=set()
    for m in input.messages:
        pid='speaker:'+(m.speaker_id or m.id)
        if pid not in seen:
            people.append(Participant(participant_id=pid,label=m.speaker_id or 'người nói chưa rõ danh tính',interaction_role='speaker'))
            seen.add(pid)
    people.append(Participant(participant_id='recipient:unknown',label='người nhận chưa rõ danh tính',interaction_role='recipient'))
    return Annotations(participants=people,spans=[],events=[],relations=[],answers_18=Answers18(**{k:AnalysisField() for k in Answers18.model_fields}))


def scope_for(message,offset,transaction=None):
    parent=message.scope_id or 'message:'+message.id
    transaction=transaction_at(message.text,offset) or transaction
    return parent+('/transaction:'+transaction if transaction else '')


def safety_extract(input):
    result=base(input)
    config=ExtractionRules.model_validate_json((DATA/'extraction_rules.json').read_text(encoding='utf-8')).model_dump()
    compiled=[(r,re.compile(r['pattern'])) for r in config['rules']]
    messages={m.id:m for m in input.messages}
    request_types={'invite_travel_or_meeting','request_secrecy','restrict_communication','demand_release_payment'}
    for message in input.messages:
        pid='speaker:'+(message.speaker_id or message.id)
        quotes=quote_ranges(message.text);seen=set()
        for unit in segments(message.text):
            context=(unit.context_start,unit.context_end)
            if context in seen:continue
            seen.add(context)
            a,b=context;raw=message.text[a:b];n=normalize(raw)
            for rule,pattern in compiled:
                for match in pattern.finditer(n.text):
                    if len(result.events)>=50:
                        result.limitations.append('Đạt giới hạn 50 sự kiện an toàn; phần còn lại chưa được phân tích.')
                        return result
                    va,vb=n.original_range(*match.span('verb'));va+=a;vb+=a
                    prefix=n.text[:match.start('verb')];kind=rule['event_type']
                    quoted=any(x<=va<y for x,y in quotes)
                    warning=bool(re.search(r'canh bao|canh giac|bai tuyen truyen|bai bao phong tranh',n.text))
                    parent=messages.get(message.parent_message_id)
                    parent_warning=message.content_type=='ocr' and parent is not None and bool(re.search(r'canh bao|canh giac|bai tuyen truyen',normalize(parent.text).text))
                    warning=warning or parent_warning
                    direct_current=bool(re.search(r'\b(?:toi|minh)\b.{0,25}(?:dang bi|hien tai bi|hien bi|bi giu|bi ep)',n.text))
                    if direct_current and not quoted and not parent_warning and not re.search(r'bai tuyen truyen|bai bao|vi du',n.text):warning=False
                    hypothetical=bool(re.search(r'gia su|bai tap|vi du mo phong',n.text) or re.search(r'giả định',raw,re.I))
                    reported=quoted or bool(re.search(r'\b(?:ho|nguoi do) (?:noi|bao)|bai bao ke|\btoi (?:doc|nghe|duoc ke)',prefix))
                    denied=bool(re.search(r'\b(?:dung|khong(?: bi| nen| duoc)?|chua)\s+(?:\w+\s+){0,2}$',prefix))
                    if kind in ('request_secrecy','restrict_communication','free_to_leave'):denied=False
                    if kind in ('threaten_harm','threaten_disclosure') and 'neu ' in prefix and match.group().startswith('se '):denied=False
                    self_report=bool(re.search(r'\b(?:toi|minh)\b',n.text)) and (kind in ('restrict_movement','impose_debt') or bool(re.search(r'\bbi\b|cua toi|cua minh',n.text))) and not reported and not warning and not hypothetical
                    role='quoted_warning' if warning else 'hypothetical' if hypothetical else 'reported' if reported else 'denial' if denied else 'request' if kind in request_types else 'claim'
                    times=list(re.finditer(r'\b(?:truoc day|tung|nam ngoai|hom qua|dang|hien tai|bay gio|hom nay|toi nay|sap)\b',n.text[:match.end()]))
                    if not times:times=list(re.finditer(r'\b(?:hien tai|bay gio|hom nay|toi nay|sap)\b',n.text[match.end():match.end()+50]))
                    timeword=times[-1].group() if times else None
                    past=timeword in ('truoc day','tung','nam ngoai','hom qua')
                    active=timeword in ('dang','hien tai','bay gio','hom nay','toi nay','sap')
                    threat=kind in ('threaten_harm','threaten_disclosure','bodily_integrity_threat')
                    temporal='hypothetical' if hypothetical else 'past' if past else 'imminent' if threat and active else 'ongoing' if active or (self_report and kind in ('restrict_movement','compel_work','compel_illegal_activity','bodily_integrity_threat') and 'se ' not in prefix) else 'planned' if re.search(r'\bse\b',prefix) else 'requested' if role=='request' else 'unknown'
                    span_id='safe:s'+str(len(result.spans)+1)
                    # Full local scope retains the state, attribution and target of the verb.
                    result.spans.append(Span(span_id=span_id,message_id=message.id,start=a,end=b,quote=raw,label='action'))
                    verb_id='safe:s'+str(len(result.spans)+1)
                    result.spans.append(Span(span_id=verb_id,message_id=message.id,start=va,end=vb,quote=message.text[va:vb],label='verb'))
                    attribution='quoted_warning' if warning else 'hypothetical' if hypothetical else 'reported' if reported else 'self_report' if self_report else 'sender_claim'
                    result.events.append(Event(event_id='safe:e'+str(len(result.events)+1),event_type=kind,
                        description=kind,actor_id=None,affected_party_id=pid if self_report else 'recipient:unknown',
                        object=message.text[va:vb],polarity='negative' if denied else 'positive',
                        modality='threat' if threat else 'conditional' if hypothetical else 'report' if self_report or reported else 'request' if role=='request' else 'assertion',
                        temporal_state=temporal,speech_role=role,
                        attribution=Attribution(speaker_id=message.speaker_id,kind=attribution),
                        status='claimed' if role not in ('quoted_warning','hypothetical') else 'observed',
                        scope_id=scope_for(message,va),event_time=timeword,evidence_refs=[span_id,verb_id],
                        extractor_rule_id=rule['id'],unknown_fields=['actor_identity','independent_verification']))
    return result


def extract(input,precheck=None):
    result=precheck.model_copy(deep=True) if precheck else safety_extract(input)
    result.relations=[]  # Rebuild once after merging both extractors; no duplicate cues.
    old=observe(input.legacy());messages={m.id:m for m in input.messages}
    # Reuse the old extractor's exact spans and actor references without copying expected labels.
    for p in old.participants:
        result.participants.append(Participant(participant_id='old:'+p.id,label=p.label,
            interaction_role='speaker' if p.role=='speaker' else 'recipient' if p.role=='addressee' else 'mentioned'))
    spans={s.id:s for s in old.evidence};event_ids=set()
    labels={'target':'object','statement':'statement'}
    for s in old.evidence:
        if s.source!='message':continue  # Context facts keep their own IDs below.
        result.spans.append(Span(span_id='old:'+s.id,message_id=s.message_id,start=s.start,end=s.end,quote=s.quote,label=labels.get(s.kind,s.kind)))
    for e in old.events:
        s=spans[e.action_span];message=messages[s.message_id];event_ids.add(e.action_id)
        attribution='quoted_warning' if e.speech_role=='quoted_warning' else 'reported' if e.speech_role=='reported' else 'sender_claim'
        role='denial' if e.speech_role=='request' and e.polarity=='negative' else e.speech_role
        parent=messages.get(message.parent_message_id)
        if message.content_type=='ocr' and parent and re.search(r'canh bao|canh giac|bai tuyen truyen',normalize(parent.text).text):
            role='quoted_warning';attribution='quoted_warning'
        result.events.append(Event(event_id='old:'+e.action_id,event_type=e.action_type,description=e.action_type,
            actor_id='old:'+e.actor if e.actor else None,recipient_id='old:'+e.recipient if e.recipient else None,
            affected_party_id='recipient:unknown',object=e.target,polarity=e.polarity,
            modality='request' if role=='request' else 'report' if role=='reported' else 'assertion',
            temporal_state=e.temporal_state,speech_role=role,attribution=Attribution(speaker_id=message.speaker_id,kind=attribution),
            status='claimed' if role in ('claim','reported') else 'observed',scope_id=scope_for(message,s.start,e.transaction_id),
            event_time=e.time_expression,evidence_refs=['old:'+r for r in e.evidence_refs],extractor_rule_id=e.rule_id,
            unknown_fields=e.limitations))
    entities={p.participant_id for p in result.participants}|{e.event_id for e in result.events}
    event_map={e.event_id:e for e in result.events}
    for r in old.relations:
        left,right='old:'+r.from_id,'old:'+r.to_id
        if left not in entities or right not in entities:continue
        scopes={event_map[e].scope_id for e in (left,right) if e in event_map}
        if len(scopes)>1:continue
        result.relations.append(Relation(relation_id='old:'+r.relation_id,type=r.type,from_id=left,to_id=right,
            evidence_refs=['old:'+s for s in r.evidence_refs],status=r.status,scope_id=next(iter(scopes)) if scopes else None,
            rationale=' '.join(r.limitations) or 'Quan hệ được bộ trích cục bộ nêu; cần rà ngữ nghĩa.',rule_id=r.rule_id))
    result.limitations.extend(old.limitations)
    result.answers_18=old.answers_18.model_copy(deep=True)
    for field in result.answers_18.__dict__.values():
        field.evidence_refs=['old:'+r for r in field.evidence_refs if r in spans and spans[r].source=='message']
        field.value.event_ids=['old:'+r for r in field.value.event_ids]
        field.value.participant_ids=['old:'+r for r in field.value.participant_ids]
        field.value.relation_ids=['old:'+r for r in field.value.relation_ids if any(x.relation_id=='old:'+r for x in result.relations)]
    # Context is a user report, never independently verified by the system.
    for c in input.context_facts:
        result.spans.append(Span(span_id='context:'+c.id,message_id=None,context_id=c.id,start=0,end=len(c.text),quote=c.text,label='statement'))
        f=result.answers_18.claims;f.status='claimed';f.evidence_refs.append('context:'+c.id)
        targets=c.applies_to_message_ids or ([input.messages[0].id] if len(input.messages)==1 else [])
        if len(targets)==1 and re.search(r'anh trai|chi gai|me toi|bo toi',normalize(c.text).text):
            m=messages[targets[0]]
            result.personal_relationships.append(PersonalRelationship(participant_ids=['speaker:'+(m.speaker_id or m.id),'recipient:unknown'],
                relationship_type='family',status='user_reported',evidence_refs=['context:'+c.id],scope_id=m.scope_id or 'message:'+m.id))
    for event in result.events:
        if event.event_type=='relationship_claim':
            message=messages[spans[event.evidence_refs[0].removeprefix('old:')].message_id]
            result.personal_relationships.append(PersonalRelationship(participant_ids=['speaker:'+(message.speaker_id or message.id),'recipient:unknown'],
                relationship_type='unknown',status='claimed',evidence_refs=event.evidence_refs,scope_id=event.scope_id))
    decorate_spans(input,result)
    link_events(result)
    fill_safety_fields(result)
    requests=[e for e in result.events if e.speech_role=='request' and e.polarity=='positive']
    all_spans={s.span_id:s for s in result.spans}
    result.answers_18.requested_actions=AnalysisField(status='observed' if requests else 'unknown',
        value=Value(statements=[all_spans[e.evidence_refs[0]].quote for e in requests[:4]],event_ids=[e.event_id for e in requests]),
        evidence_refs=list(dict.fromkeys(s for e in requests for s in e.evidence_refs)))
    return result


def decorate_spans(input,result):
    patterns={'state':r'\b(?:da|chua|dang|cho)\b','time':r'\b(?:hom nay|hom qua|toi nay|hien tai|bay gio|nam ngoai)\b',
        'condition':r'\b(?:neu|thi|truoc khi|sau khi|moi)\b','purpose':r'\bde\b',
        'participant':r'\b(?:toi|ban|ho|nguoi nhan|nguoi gui)\b',
        'organization':r'\b(?:cong an|ngan hang|cong ty)\b','account':r'\btai khoan\b',
        'application':r'\b(?:ung dung|apk)\b','reported_speech':r'\b(?:ho noi|nguoi gui noi|toi nghe)\b',
        'persuasion':r'\b(?:giu bi mat|de doa|hoa hong|thu nhap cao|neu khong)\b'}
    for m in input.messages:
        n=normalize(m.text)
        for label,pattern in patterns.items():
            for match in re.finditer(pattern,n.text):
                a,b=n.original_range(*match.span())
                result.spans.append(Span(span_id='tag:s'+str(len(result.spans)+1),message_id=m.id,start=a,end=b,quote=m.text[a:b],label=label))
        for a,b in quote_ranges(m.text):
            result.spans.append(Span(span_id='tag:s'+str(len(result.spans)+1),message_id=m.id,start=a,end=b,quote=m.text[a:b],label='quotation'))
        for match in re.finditer(r'https?://[^\s<>]+',m.text):
            result.spans.append(Span(span_id='tag:s'+str(len(result.spans)+1),message_id=m.id,start=match.start(),end=match.end(),quote=match.group(),label='url'))


def link_events(result):
    spans={s.span_id:s for s in result.spans}
    pairs={('invite_travel_or_meeting','request_secrecy'):'travel_conditioned_on_secrecy',
        ('impose_debt','restrict_movement'):'movement_restricted_by_debt',
        ('retain_identity_documents','restrict_movement'):'document_retention_limits_exit',
        ('threaten_harm','compel_work'):'threat_used_to_compel_action',
        ('threaten_harm','compel_illegal_activity'):'threat_used_to_compel_action',
        ('offer_employment','change_destination_or_terms'):'work_differs_from_agreement'}
    for a in result.events:
        for b in result.events:
            kind=pairs.get((a.event_type,b.event_type))
            if not kind or not a.scope_id or a.scope_id!=b.scope_id:continue
            if a.affected_party_id!=b.affected_party_id or a.polarity!='positive' or b.polarity!='positive':continue
            if a.speech_role in ('quoted_warning','hypothetical','denial') or b.speech_role in ('quoted_warning','hypothetical','denial'):continue
            common_context=any(x.message_id==y.message_id and x.message_id is not None and max(x.start,y.start)<min(x.end,y.end)
                for x in (spans[s] for s in a.evidence_refs) for y in (spans[s] for s in b.evidence_refs))
            if not common_context and a.affected_party_id=='recipient:unknown' and kind!='work_differs_from_agreement':continue
            result.relations.append(Relation(relation_id='linked:r'+str(len(result.relations)+1),type=kind,
                from_id=a.event_id,to_id=b.event_id,evidence_refs=list(dict.fromkeys(a.evidence_refs+b.evidence_refs)),
                status='inferred',scope_id=a.scope_id,rationale='Hai dấu hiệu cùng phạm vi và người bị tác động; chưa chứng minh một vụ án.',rule_id='LINK-'+kind))
    # Payment-for-release is already one bounded event with both clauses quoted.
    for e in result.events:
        if e.event_type=='demand_release_payment' and e.polarity=='positive' and e.speech_role not in ('quoted_warning','hypothetical'):
            result.relations.append(Relation(relation_id='linked:r'+str(len(result.relations)+1),type='release_conditioned_on_payment',
                from_id=e.event_id,to_id=e.event_id,evidence_refs=e.evidence_refs,status='claimed',scope_id=e.scope_id,
                rationale='Điều kiện do bên đòi tiền nêu, không chứng minh người bị giữ thật.',rule_id='LINK-RELEASE'))
    by_id={e.event_id:e for e in result.events}
    financial={'transfer_funds','receive_funds','withdraw_funds','handover_asset','provide_code','code_identity'}
    for relation in list(result.relations):
        if relation.type not in ('before','after','prerequisite_for','state_update'):continue
        left=by_id.get(relation.from_id);right=by_id.get(relation.to_id)
        if not left or not right or left.event_id==right.event_id:continue
        if left.event_type not in financial or right.event_type not in financial or left.scope_id!=right.scope_id:continue
        if any(e.speech_role in ('quoted_warning','hypothetical') for e in (left,right)):continue
        if any(r.type=='same_transaction' and {r.from_id,r.to_id}=={left.event_id,right.event_id} for r in result.relations):continue
        result.relations.append(Relation(relation_id='linked:r'+str(len(result.relations)+1),type='same_transaction',
            from_id=left.event_id,to_id=right.event_id,evidence_refs=relation.evidence_refs,status='inferred',scope_id=left.scope_id,
            rationale='Quan hệ thời gian/điều kiện cùng phạm vi hỗ trợ cùng giao dịch; nhãn yếu cần người rà.',rule_id='LINK-SAME-TRANSACTION'))


def fill_safety_fields(result):
    safety=[e for e in result.events if e.event_id.startswith('safe:')]
    mapping={'situation':safety,'claims':[e for e in safety if e.speech_role in ('claim','reported')],
        'requested_actions':[e for e in safety if e.speech_role=='request' and e.polarity=='positive'],
        'assets_and_access':[e for e in safety if e.event_type in ('retain_identity_documents','restrict_movement','restrict_communication','bodily_integrity_threat','threaten_harm','compel_work','compel_illegal_activity')],
        'persuasion':[e for e in safety if e.event_type in ('build_trust','impose_debt','request_secrecy','threaten_harm','threaten_disclosure')],
        'communication_channel':[e for e in safety if e.event_type=='restrict_communication'],
        'action_targets':[e for e in safety if e.affected_party_id or e.actor_id],
        'contradictions_and_alternatives':[e for e in safety if e.polarity=='negative' or e.speech_role=='quoted_warning' or e.event_type in ('consent_and_exit_available','free_to_leave','return_documents_available')],
        'benefit_and_mismatch':[e for e in safety if any(r.type=='work_differs_from_agreement' and e.event_id in (r.from_id,r.to_id) for r in result.relations)]}
    spans={s.span_id:s for s in result.spans}
    for key,events in mapping.items():
        if not events:continue
        f=getattr(result.answers_18,key);f.status='claimed' if key=='claims' else 'inferred'
        f.value.event_ids=list(dict.fromkeys(f.value.event_ids+[e.event_id for e in events]))
        f.evidence_refs=list(dict.fromkeys(f.evidence_refs+[r for e in events for r in e.evidence_refs]))
        f.value.statements=list(dict.fromkeys(f.value.statements+[spans[e.evidence_refs[0]].quote for e in events[:3]]))
    if safety:
        f=result.answers_18.participants;f.status='observed'
        f.value.participant_ids=list(dict.fromkeys(f.value.participant_ids+[p for e in safety for p in (e.actor_id,e.affected_party_id) if p]))
        f.evidence_refs=list(dict.fromkeys(f.evidence_refs+[r for e in safety for r in e.evidence_refs]))
        f.value.statements=list(dict.fromkeys(f.value.statements+['Vai và người bị tác động theo nội dung khai báo; danh tính ngoài đời chưa được xác minh.']))
        f=result.answers_18.evidence_quality;f.status='observed'
        f.evidence_refs=list(dict.fromkeys(f.evidence_refs+[r for e in safety for r in e.evidence_refs]))
        f.value.statements=list(dict.fromkeys(f.value.statements+['Quote đối chiếu bản gốc; không chứng minh lời khai hoặc danh tính là thật.']))
    if result.personal_relationships:
        f=result.answers_18.relationship;f.status='claimed'
        f.evidence_refs=list(dict.fromkeys(r for p in result.personal_relationships for r in p.evidence_refs))
        f.value.participant_ids=list(dict.fromkeys(p for r in result.personal_relationships for p in r.participant_ids))
        f.value.statements=['Quan hệ được tự nhận hoặc do người dùng báo, chưa được hệ thống xác minh độc lập.']
    if result.relations:
        f=result.answers_18.conditions_and_sequence;f.status='inferred'
        f.value.relation_ids=[r.relation_id for r in result.relations]
        f.evidence_refs=list(dict.fromkeys(x for r in result.relations for x in r.evidence_refs))
