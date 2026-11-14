"""One extraction pass for banking display instructions, before any rule evaluation."""
import re
from ..local_observation.text import normalize
from ..local_observation.segmentation import segments
from .schema import Span,Event,Attribution,Relation
from .extract import scope_for


def extend_banking(input,a):
    messages={m.id:m for m in input.messages};order={m.id:i for i,m in enumerate(input.messages)}
    spans={s.span_id:s for s in a.spans}
    for m in input.messages:
        # Most messages have no banking-display content. Avoid repeating the
        # segmentation pass unless this extraction family is relevant.
        normalized=normalize(m.text).text
        if not any(t in normalized for t in ('ung dung ngan hang','so du','lich su giao dich','thong tin ngan hang')):continue
        for segment in segments(m.text):
            raw=m.text[segment.context_start:segment.context_end];text=normalize(raw).text
            # Treat the entire local context as the evidence; no new text is fabricated.
            if not re.search(r'\b(?:mo|vao|xem|hien thi)\b.{0,65}\b(?:ung dung ngan hang|so du|lich su giao dich|thong tin ngan hang)\b',text):continue
            if any(e.extractor_rule_id=='FACT-BANK-INFO-1' and any(spans[s].message_id==m.id and spans[s].start==segment.context_start for s in e.evidence_refs) for e in a.events):continue
            warning=segment.quoted or 'canh bao' in text or 'canh giac' in text
            denied=bool(re.search(r'\b(?:dung|khong nen|khong duoc)\s+(?:mo|vao|xem)',text))
            claim=bool(re.search(r'\b(?:toi|minh)\s+(?:da|tu|dang)\s+mo',text))
            role='quoted_warning' if warning else 'denial' if denied else 'claim' if claim else 'request'
            sid='bank:s'+str(len(a.spans)+1);eid='bank:e'+str(len(a.events)+1)
            span=Span(span_id=sid,message_id=m.id,start=segment.context_start,end=segment.context_end,quote=raw,label='action')
            a.spans.append(span);spans[sid]=span
            a.events.append(Event(event_id=eid,event_type='other',description='bank_information_open_requested',actor_id=None,
                affected_party_id='recipient:unknown',object='bank_information',polarity='negative' if denied else 'positive',
                modality='request' if role=='request' else 'assertion',temporal_state='requested' if role=='request' else 'unknown',
                speech_role=role,attribution=Attribution(speaker_id=m.speaker_id,kind='quoted_warning' if warning else 'sender_claim'),
                status='observed',scope_id=scope_for(m,segment.context_start),evidence_refs=[sid],extractor_rule_id='FACT-BANK-INFO-1'))
            if role=='request':
                f=a.answers_18.requested_actions;f.value.event_ids.append(eid);f.evidence_refs.append(sid);f.value.statements.append(raw)
    screens=[e for e in a.events if e.event_type=='share_screen' and e.speech_role=='request' and e.polarity=='positive']
    banks=[e for e in a.events if e.extractor_rule_id=='FACT-BANK-INFO-1' and e.speech_role=='request' and e.polarity=='positive']
    for bank in banks:
        bm=spans[bank.evidence_refs[0]].message_id
        for screen in screens:
            sm=spans[screen.evidence_refs[0]].message_id
            if screen.scope_id!=bank.scope_id or screen.affected_party_id!=bank.affected_party_id:continue
            if order[sm]>order[bm] or order[bm]-order[sm]>2:continue
            same_message=sm==bm
            same_claimant=messages[sm].speaker_id is not None and messages[sm].speaker_id==messages[bm].speaker_id
            if not same_message and not same_claimant:continue
            link_text=normalize('\n'.join(m.text for m in input.messages[order[sm]:order[bm]+1])).text
            if not re.search(r'sau khi chia se|chia se man hinh.{0,100}\broi\b|sau do|tiep theo',link_text,re.S):continue
            # A supporting sequence is observed in the dialogue, not inferred from
            # extension arrival timestamps. Preserve the linkage text as evidence.
            refs=list(dict.fromkeys(screen.evidence_refs+bank.evidence_refs))
            for middle in input.messages[order[sm]+1:order[bm]]:
                if 'sau khi chia se' in normalize(middle.text).text:
                    sid='bank:link:'+middle.id
                    if sid not in spans:
                        s=Span(span_id=sid,message_id=middle.id,start=0,end=len(middle.text),quote=middle.text,label='statement')
                        spans[sid]=s;a.spans.append(s)
                    refs.append(sid)
            a.relations.append(Relation(relation_id='bank:r'+str(len(a.relations)+1),type='after',from_id=bank.event_id,to_id=screen.event_id,
                evidence_refs=refs,status='inferred',scope_id=bank.scope_id,rationale='Yêu cầu nối tiếp có dấu chỉ sau khi chia sẻ; chưa xác minh danh tính.',rule_id='REL-SCREEN-BANK-SEQUENCE'))
    return a
