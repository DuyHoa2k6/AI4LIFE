"""Explicit user-reported updates, scoped and attributed; not bank verification."""
import re
from ..local_observation.text import normalize,quote_ranges
from .schema import Event,Attribution,Participant,Relation


def apply_user_updates(input,a):
    spans={s.span_id:s for s in a.spans};events=list(a.events)
    user_id='user:clarification'
    for context in input.context_facts:
        text=normalize(context.text).text;ref='context:'+context.id
        if ref not in spans:continue
        targets=set(context.applies_to_message_ids) or ({input.messages[0].id} if len(input.messages)==1 else set())
        candidates=[e for e in events if any(spans[s].message_id in targets for s in e.evidence_refs if s in spans)]
        scopes={e.scope_id for e in candidates}
        scope=context.scope_id or (next(iter(scopes)) if len(scopes)==1 else None)
        if scope is None or (scopes and scope not in scopes):continue
        if '/transaction:' in scope:
            mentioned={m.group() for m in re.finditer(r'\b(?:don|giao dich|hop dong)\s+[a-z0-9]+\b',text)}
            if mentioned and mentioned!={scope.split('/transaction:',1)[1]}:continue
        candidates=[e for e in candidates if e.scope_id==scope]
        if quote_ranges(context.text) or re.search(r'canh bao|gia su|\bneu\b',text):continue
        third_party=bool(re.search(r'nguoi mua noi|ho noi|nguoi gui noi',text))
        received=bool(re.search(r'\b(?:da nhan du tien|nhan du tien|tien da vao tai khoan)\b',text))
        negative=bool(re.search(r'\b(?:chua|khong)\s+(?:\w+\s+){0,3}(?:nhan|thay|xac nhan|tien)\b',text))
        checked=bool(re.search(r'\btoi (?:da )?(?:tu )?kiem tra\b',text))
        code=bool(re.search(r'ma dang nhap|ma xac thuc|\botp\b',text))
        if not ((received or negative) and any(e.event_type in ('receive_funds','handover_asset') for e in candidates) or code and any(e.event_type=='provide_code' for e in candidates)):continue
        if not any(p.participant_id==user_id for p in a.participants):
            a.participants.append(Participant(participant_id=user_id,label='Người dùng cung cấp thông tin bổ sung',interaction_role='speaker',
                identity_status='user_reported',information_status='user_reported',evidence_refs=[ref]))
        eid='context:event:'+context.id
        if code:
            kind='code_identity';state='unknown';polarity='positive'
        else:kind='receive_funds';state='pending' if negative else 'completed';polarity='negative' if negative else 'positive'
        update=Event(event_id=eid,event_type=kind,description='Thông tin do người dùng bổ sung, chưa xác minh độc lập',actor_id=user_id,
            affected_party_id='recipient:unknown',polarity=polarity,modality='report',temporal_state=state,speech_role='reported' if third_party else 'claim',
            attribution=Attribution(speaker_id=None,kind='user_report',verification_status='user_reports_verification' if checked else 'unverified'),
            status='claimed',scope_id=scope,evidence_refs=[ref],extractor_rule_id='USER-REPORTED-UPDATE')
        a.events.append(update)
        for old in candidates:
            if code and old.event_type=='provide_code' and old.speech_role=='request' or not code and checked and received and not negative and not third_party and old.event_type=='receive_funds' and old.polarity=='negative':
                a.relations.append(Relation(relation_id='context:r'+str(len(a.relations)+1),type='state_update',from_id=old.event_id,to_id=eid,
                    evidence_refs=list(dict.fromkeys(old.evidence_refs+[ref])),status='inferred',scope_id=scope,
                    rationale='Người dùng cập nhật dữ kiện cho đúng tình huống; không dùng thời điểm thu thập làm thời điểm sự kiện.',rule_id='LINK-USER-REPORTED-UPDATE'))
            if not code and checked and received and not negative and not third_party and old.event_type=='handover_asset':
                a.relations.append(Relation(relation_id='context:r'+str(len(a.relations)+1),type='before',from_id=eid,to_id=old.event_id,
                    evidence_refs=list(dict.fromkeys([ref]+old.evidence_refs)),status='inferred',scope_id=scope,
                    rationale='Người dùng báo đã nhận tiền trước khi làm theo yêu cầu còn hiệu lực.',rule_id='REL-REPORTED-PAYMENT-FIRST'))
            if not code and negative and not third_party and old.event_type=='handover_asset' and old.speech_role=='request':
                a.relations.append(Relation(relation_id='context:r'+str(len(a.relations)+1),type='before',from_id=old.event_id,to_id=eid,
                    evidence_refs=list(dict.fromkeys(old.evidence_refs+[ref])),status='inferred',scope_id=scope,
                    rationale='Người dùng báo thanh toán chưa xác nhận trong khi yêu cầu giao tài sản còn hiệu lực.',rule_id='LINK-USER-UNPAID-HANDOVER'))
    return a
