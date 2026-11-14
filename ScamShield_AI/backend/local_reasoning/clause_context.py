"""Bounded local clause roles and contextual links; no identity verification.

Unknown names have stable role labels. A risk rule requires an active request,
a textual affected role and explicit links within one source and situation.
"""
import re
from ..local_observation.segmentation import segments
from ..local_observation.text import normalize, quote_ranges
from .extract import scope_for
from .schema import Span, Event, Attribution, Relation, Participant
from .interpretation_schema import ClauseRole, SalientAction

INACTIVE = {'quoted_warning', 'hypothetical', 'denial', 'reported', 'unknown'}
PATTERNS = [
    ('account_change', 'other', r'tai khoan (?:nhan tien )?(?:vua |da )?(?:doi|thay doi)|tai khoan (?:dung|mang) ten nguoi khac'),
    ('payment_instruction', 'transfer_funds', r'\b(?:ban|anh|chi|em)\s+(?:hay |cu |vui long )?chuyen\b[^.!?;]{0,95}(?:thong tin|tai khoan|tien)'),
    ('verification_delay', 'avoid_verification', r'\b(?:dung goi|khoi goi|chua can goi)[^.!?;]*|\b(?:ngay mai|toi nay|sau do)[^.!?;]{0,35}(?:goi|xac nhan|xac minh)|\bchuyen[^.!?;]{0,55}truoc[^.!?;]{0,45}(?:xac minh|xac nhan)[^.!?;]{0,15}sau'),
    ('travel_request', 'invite_travel_or_meeting', r'\b(?:cu|hay|ban can|ban phai)\s+(?:di|len|sang)[^.!?;]{0,65}(?:gap|tuyen dung|lam viec)|\b(?:ban|anh|chi|em)\s+(?:hay )?di\s+(?:gap|lam viec)[^.!?;]*'),
    ('contract_deferred', 'change_destination_or_terms', r'\b(?:chua|khong) can (?:xem|doc|ky) hop dong\b'),
    ('documents_custody', 'retain_identity_documents', r'\b(?:giay to(?: ca nhan)?|ho chieu|can cuoc|cccd)\b[^.!?;]{0,55}\b(?:giao|dua|nop)\b[^.!?;]{0,65}\bgiu\b[^.!?;]*|\b(?:giao|dua|nop)\b[^.!?;]{0,45}(?:giay to|ho chieu|can cuoc|cccd)[^.!?;]{0,60}\bgiu\b[^.!?;]*'),
    ('secrecy', 'request_secrecy', r'\b(?:dung|khong duoc|cho)\s+(?:ke|noi|bao)[^.!?;]{0,45}\b(?:gia dinh|nguoi than|bo me)\b'),
    ('payment_confirmed', 'receive_funds', r'\b(?:tien|khoan tien|khoan thanh toan)\b[^.!?;]{0,65}\b(?:da vao du|da vao tai khoan|da nhan du)\b|\b(?:da|vua)\s+(?:nhan du|nhan duoc du)\s+tien\b'),
]
COMPILED = [(name, kind, re.compile(pattern)) for name, kind, pattern in PATTERNS]


def units(input):
    for m in input.messages:
        source = 'speaker:' + (m.speaker_id or m.id)
        seen = set()
        for seg in segments(m.text):
            key = (seg.context_start, seg.context_end)
            if key in seen:
                continue
            seen.add(key)
            start, end = key
            raw = m.text[start:end]
            label = re.match(r'\s*(Người bán|Người mua|Người gửi|Người nhận)\s*:', raw, re.I)
            if label:
                source = 'text-role:' + normalize(label.group(1)).text + ':' + (m.scope_id or m.id)
            yield m, start, end, raw, source


def extend_clause_context(input, a, frames):
    """Attach only evidence-bearing observations and explicit contextual links."""
    spans = {s.span_id: s for s in a.spans}
    records = []
    warning_headers = {m.id for m in input.messages if re.match(r'\s*(?:canh bao\s*:|gia su trong bai tap\s*:)',normalize(m.text).text)
        and not re.search(r'\b(?:toi|minh) dang bi|nhung bay gio toi|con toi hien',normalize(m.text).text)}
    for e in a.events:
        if any(s in spans and spans[s].message_id in warning_headers for s in e.evidence_refs):
            e.speech_role='quoted_warning';e.attribution.kind='quoted_warning'
    for frame in frames:
        if next((e for e in a.events if e.event_id == frame.action_event_id and e.speech_role=='quoted_warning'),None):
            frame.speech_role='quoted_warning'
    for m, start, end, raw, source in units(input):
        if len(records) >= 80:
            a.limitations.append('Đạt giới hạn 80 cụm vai trò; phần còn lại chưa kiểm tra đầy đủ.')
            break
        n = normalize(raw).text
        matches = [(name, kind, pattern.search(n)) for name, kind, pattern in COMPILED]
        matches = [(name, kind, match) for name, kind, match in matches if match]
        if not matches:
            continue
        sid = 'clause:s' + str(len(a.spans) + 1)
        span = Span(span_id=sid, message_id=m.id, start=start, end=end, quote=raw, label='statement')
        a.spans.append(span); spans[sid] = span
        if source not in {p.participant_id for p in a.participants}:
            a.participants.append(Participant(participant_id=source, label=source.split(':')[1], interaction_role='speaker', evidence_refs=[sid]))
        scope = scope_for(m, start)
        quoted = any(max(start, x) < min(end, y) for x, y in quote_ranges(m.text))
        parent = next((p for p in input.messages if p.id == m.parent_message_id), None)
        inactive = m.id in warning_headers or quoted or bool(re.search(r'canh bao|canh giac|dung lam theo|gia su|vi du|neu co ai|toi (?:nghe|doc)|ho (?:noi|bao)', n))
        inactive = inactive or bool(parent and m.content_type == 'ocr' and re.search(r'canh bao|canh giac', normalize(parent.text).text))
        record = {'source': source, 'scope': scope, 'message': m.id, 'start': start, 'end': end, 'raw': n, 'events': [], 'sid': sid}
        for name, kind, match in matches:
            prefix = n[:match.start()]
            negated = bool(re.search(r'\b(?:dung|khong(?: nen| duoc)?|chua)\s*$', prefix)) and name not in ('contract_deferred','secrecy','verification_delay')
            if name == 'documents_custody' and re.search(r'\b(?:dung|khong (?:nen|duoc))\b.{0,35}\b(?:giao|dua|nop)\b',n):negated=True
            role = 'quoted_warning' if inactive else 'denial' if negated else 'claim' if name in ('account_change','payment_confirmed') else 'request'
            # Account changes are assertions, not verification. A confirmed
            # payment must be a first-person check, not a buyer's reassurance.
            if name == 'payment_confirmed' and not re.search(r'\b(?:toi|minh)\b.{0,45}(?:kiem tra|nhan du)|\btoi da nhan du', n):
                role = 'unknown'
            if name == 'payment_confirmed' and ('nguoi mua' in source or m.speaker_id in ('buyer','người mua')):
                role = 'unknown'
            if name == 'documents_custody' and re.search(r'(?:co the|duoc|bat cu luc nao).{0,30}(?:lay lai|tra lai)|giu ho|giu giup', n):
                role = 'unknown'
            if name == 'documents_custody' and re.search(r'giay to cua (?:nguoi khac|anh ay|chi ay|ho)\b',n):role='unknown'
            e = Event(event_id='clause:e' + str(len(a.events) + 1), event_type=kind,
                description=name, actor_id='recipient:unknown' if role == 'request' else source,
                affected_party_id='recipient:unknown', object=match.group(), polarity='negative' if negated else 'positive',
                modality='request' if role == 'request' else 'assertion', temporal_state='completed' if name == 'payment_confirmed' else 'requested' if role == 'request' else 'unknown',
                speech_role=role, attribution=Attribution(speaker_id=m.speaker_id, kind='quoted_warning' if inactive else 'sender_claim'),
                status='observed' if role == 'request' else 'claimed' if role == 'claim' else 'unknown', scope_id=scope,
                evidence_refs=[sid], extractor_rule_id='CLAUSE-' + name.upper(), unknown_fields=['real_identity'])
            a.events.append(e); record['events'].append(e)
            if name == 'documents_custody':
                custodian = 'custodian:unknown:' + scope
                if custodian not in {p.participant_id for p in a.participants}:
                    a.participants.append(Participant(participant_id=custodian, label='bên nhận giữ giấy tờ, chưa rõ danh tính', interaction_role='mentioned', evidence_refs=[sid]))
                e.actor_id = custodian
                e.recipient_id = custodian
        records.append(record)

    def link(kind, left, right, rule):
        if left.scope_id != right.scope_id or left.affected_party_id != right.affected_party_id:
            return
        if any(r.type == kind and r.from_id == left.event_id and r.to_id == right.event_id for r in a.relations):
            return
        a.relations.append(Relation(relation_id='clause:r' + str(len(a.relations) + 1), type=kind,
            from_id=left.event_id, to_id=right.event_id, evidence_refs=list(dict.fromkeys(left.evidence_refs + right.evidence_refs)),
            status='inferred', scope_id=left.scope_id, rationale='Quan hệ trong các cụm có cùng nguồn, phạm vi và vai trò bị tác động; không xác minh danh tính.', rule_id=rule))

    for record in records:
        events = [e for e in record['events'] if e.speech_role not in INACTIVE and e.polarity == 'positive']
        same = [r for r in records if r['source'] == record['source'] and r['scope'] == record['scope'] and r['message'] == record['message'] and abs(r['start'] - record['start']) <= 500]
        peers = [e for r in same for e in r['events'] if e.speech_role not in INACTIVE and e.polarity == 'positive']
        for e in events:
            if e.description == 'payment_instruction':
                for p in peers:
                    if p.description == 'account_change':link('same_transaction', e, p, 'LINK-PAYMENT-ACCOUNT-CHANGE')
                    if p.description == 'verification_delay':link('before', e, p, 'LINK-PAYMENT-BEFORE-VERIFY')
            if e.description == 'travel_request':
                for p in peers:
                    if p.description == 'secrecy':link('travel_conditioned_on_secrecy', e, p, 'LINK-TRAVEL-SECRECY')
                    if p.description == 'documents_custody':link('prerequisite_for', e, p, 'LINK-TRAVEL-DOCUMENT-CUSTODY')
                    if p.description == 'contract_deferred':link('before', e, p, 'LINK-TRAVEL-BEFORE-CONTRACT')
            if e.description == 'payment_confirmed':
                # Explicit first-person temporal update, same named speaker.
                if not re.search(r'vua kiem tra lai|kiem tra lai|bay gio|hien tai', record['raw']):continue
                for old in a.events:
                    if old.event_type != 'receive_funds' or old.polarity != 'negative' or old.scope_id != e.scope_id:continue
                    locations = [spans[s] for s in old.evidence_refs if s in spans and spans[s].message_id == record['message']]
                    for loc in locations:
                        if loc.start >= record['start']:continue
                        old_record = next((r for m, s, en, raw, src in units(input) if m.id == loc.message_id and s <= loc.start < en for r in [{'source': src, 'raw': normalize(raw).text}]), None)
                        if old_record and old_record['source'] == record['source'] and re.search(r'luc sang|truoc do|khi nay|ban dau', old_record['raw']):
                            link('state_update', old, e, 'LINK-EXPLICIT-PAYMENT-UPDATE')
                for handover in a.events:
                    if handover.event_type != 'handover_asset' or handover.speech_role != 'request' or handover.scope_id != e.scope_id:continue
                    locations = [spans[s] for s in handover.evidence_refs if s in spans]
                    if any(s.message_id == record['message'] and s.start >= record['end'] for s in locations):
                        link('before', e, handover, 'REL-REPORTED-PAYMENT-FIRST')
    return a


def add_role_and_salience(input, a, interpretation):
    spans = {s.span_id: s for s in a.spans}
    # A textual addressee is a role, not a verified person or a proven victim.
    for m, start, end, raw, source in units(input):
        events = [e for e in a.events if any(s in spans and spans[s].message_id == m.id and start <= spans[s].start < end for s in e.evidence_refs)]
        if not events:continue
        direct = [e for e in events if e.speech_role == 'request' and e.polarity == 'positive']
        known_target = bool(direct and re.search(r'\b(?:ban|anh|chi|em|dung|hay|cu)\b', normalize(raw).text))
        imperative = re.sub(r'^\s*(?:nguoi gui|nguoi nhan|nguoi mua|nguoi ban)\s*:\s*','',normalize(raw).text).strip()
        if direct and re.match(r'(?:doc|gui|chuyen|giao|cai|bam|mo|nhap)\b',imperative):known_target=True
        if direct and any(e.description == 'documents_custody' for e in direct):known_target = True
        refs = list(dict.fromkeys(s for e in events for s in e.evidence_refs if s in spans and spans[s].message_id == m.id and start <= spans[s].start < end))
        custody = next((e for e in direct if e.description == 'documents_custody'),None)
        primary=direct[0] if direct else None
        interpretation.clause_roles.append(ClauseRole(clause_id=m.id + ':' + str(start), scope_id=events[0].scope_id,
            evidence_refs=refs, requester_id=primary.semantic.requester_id if primary and primary.semantic else source if direct else None, performer_id=primary.actor_id if known_target else None,
            affected_party_id=primary.affected_party_id if known_target else None, affected_role='bên bị tác động theo sự kiện đã gắn vai' if known_target else 'unknown',
            affected_status='textual_role' if known_target else 'unknown', unresolved_roles=['real_identity'] + ([] if known_target else ['affected_party']), event_refs=[e.event_id for e in events],
            role_labels={'requester':'nguồn yêu cầu trong văn bản; chưa xác minh danh tính',
                'affected_party':'người được yêu cầu chuyển tiền, giao tài sản hoặc giấy tờ' if known_target else 'chưa xác định được bên bị tác động',
                **({'custodian':custody.actor_id} if custody else {})}))
    # Select contextual consequences, never the most frequent verb or a score.
    for r in a.relations:
        label = {
            'LINK-PAYMENT-BEFORE-VERIFY': ('Có thể chuyển tiền vào tài khoản chưa xác minh.', 'Yêu cầu chuyển tiền xảy ra trước bước xác minh.'),
            'LINK-TRAVEL-DOCUMENT-CUSTODY': ('Có thể mất quyền kiểm soát giấy tờ và khó rời khỏi nơi làm việc.', 'Di chuyển gắn với giao giấy tờ để bên đón giữ.'),
            'CTX-PAYMENT-CONDITION': ('Có thể mất thêm tiền để theo đuổi khoản tiền được hứa trả.', 'Hành động nộp tiền là điều kiện để nhận lại tiền.'),
            'CTX-HANDOVER-BEFORE-PAYMENT': ('Có thể mất tài sản khi chưa xác nhận thanh toán.', 'Yêu cầu giao tài sản trước trạng thái thanh toán chưa xác nhận.'),
        }.get(r.rule_id)
        if not label:continue
        endpoints = [next(e for e in a.events if e.event_id == ref) for ref in (r.from_id,r.to_id)]
        if any(e.speech_role in INACTIVE or e.polarity != 'positive' for e in endpoints):continue
        interpretation.salient_actions.append(SalientAction(scope_id=r.scope_id,event_refs=[r.from_id],supporting_relation_refs=[r.relation_id],
            affected_party_id=endpoints[0].affected_party_id,consequence=label[0],selection_reason=label[1],rule_id=r.rule_id))
    # One primary action per situation: explicit loss of autonomy takes
    # precedence over a supporting payment/pressure cue, without adding scores.
    precedence = ['LINK-TRAVEL-DOCUMENT-CUSTODY','CTX-PAYMENT-CONDITION','LINK-PAYMENT-BEFORE-VERIFY','CTX-HANDOVER-BEFORE-PAYMENT']
    for scope in {s.scope_id for s in interpretation.salient_actions}:
        items = [s for s in interpretation.salient_actions if s.scope_id == scope]
        min(items,key=lambda s:precedence.index(s.rule_id)).is_primary = True
    covered = {s.scope_id for s in interpretation.salient_actions}
    action_order = ['provide_credentials','provide_code','retain_identity_documents','grant_control','share_screen','transfer_funds','handover_asset']
    for scope in {e.scope_id for e in a.events} - covered:
        active = [e for e in a.events if e.scope_id==scope and e.speech_role=='request' and e.polarity=='positive'
            and e.event_type in action_order and any(c.affected_status=='textual_role' and e.event_id in c.event_refs for c in interpretation.clause_roles)]
        if not active:continue
        selected = min(active,key=lambda e:action_order.index(e.event_type))
        links = [r.relation_id for r in a.relations if selected.event_id in (r.from_id,r.to_id)]
        consequence = next((c.description for c in interpretation.consequences if selected.event_id in c.action_refs),
            'Cần làm rõ tác động của yêu cầu; chưa đủ quan hệ để kết luận nguy hiểm.')
        interpretation.salient_actions.append(SalientAction(scope_id=scope,event_refs=[selected.event_id],supporting_relation_refs=links,
            affected_party_id=selected.affected_party_id,consequence=consequence,selection_reason='Ưu tiên yêu cầu tác động đến tài khoản, giấy tờ hoặc tài sản; đây không phải kết luận mức rủi ro.',
            rule_id='SELECT-DIRECT-IMPACT',is_primary=True))
    return interpretation


def assess_contextual_choices(a, interpretation, assessment):
    """Levels 3/4 require a linked detrimental choice, not an unknown identity."""
    events = {e.event_id: e for e in a.events}
    def linked(rule):return [r for r in a.relations if r.rule_id == rule and all(events[x].speech_role not in INACTIVE and events[x].polarity == 'positive' for x in (r.from_id,r.to_id))]
    candidates = []
    for payment in linked('LINK-PAYMENT-BEFORE-VERIFY'):
        accounts = [r for r in linked('LINK-PAYMENT-ACCOUNT-CHANGE') if r.from_id == payment.from_id]
        if accounts:
            candidates.append(('suspicious','R-CLAUSE-PAYMENT-VERIFY',[payment,*accounts],
                'Người gửi yêu cầu chuyển tiền theo tài khoản thay đổi hoặc khác tên trước khi xác minh qua kênh quen dùng.',
                'Xác nhận tài khoản nhận tiền qua đầu mối đã biết trước khi chuyển.'))
    for custody in linked('LINK-TRAVEL-DOCUMENT-CUSTODY'):
        secrecy = [r for r in linked('LINK-TRAVEL-SECRECY') if r.from_id == custody.from_id]
        contract = [r for r in linked('LINK-TRAVEL-BEFORE-CONTRACT') if r.from_id == custody.from_id]
        if secrecy and contract:
            candidates.append(('high','R-CLAUSE-TRAVEL-CONTROL',[custody,*secrecy,*contract],
                'Yêu cầu đi gặp tuyển dụng khi chưa xem hợp đồng, giấu gia đình và giao giấy tờ để người đón giữ có thể làm bạn bị cô lập và mất quyền chủ động rời đi. Chưa xác minh đã xảy ra cưỡng ép hoặc mua bán người.',
                'Tạm dừng di chuyển và giao giấy tờ; cùng người tin cậy xác minh đơn vị tuyển dụng, hợp đồng và quyền lấy lại giấy tờ.'))
        elif secrecy:
            candidates.append(('suspicious','R-CLAUSE-TRAVEL-CUSTODY',[custody,*secrecy],
                'Yêu cầu đi gặp kèm giữ bí mật và giao giấy tờ cho bên đón giữ có thể hạn chế khả năng tìm hỗ trợ.',
                'Xác minh công việc cùng người tin cậy trước khi đi; làm rõ ai giữ giấy tờ và quyền lấy lại.'))
    rank = {'clear':1,'need_context':2,'suspicious':3,'high':4}
    for risk, rule, relations, summary, action in sorted(candidates,key=lambda c:-rank[c[0]]):
        if rank[risk] < rank.get(assessment.risk_status,0):continue
        action_ids = {r.from_id for r in relations}
        if not any(c.affected_status == 'textual_role' and action_ids.intersection(c.event_refs) for c in interpretation.clause_roles):continue
        if assessment.safety_urgency == 'urgent':continue
        assessment.risk_status=risk;assessment.summary=summary;assessment.recommended_actions=[action]
        assessment.applicable_rule_ids=list(dict.fromkeys([rule,*assessment.applicable_rule_ids]))
        assessment.evidence_refs=list(dict.fromkeys(assessment.evidence_refs+[s for r in relations for s in r.evidence_refs]))
        assessment.supported_conclusions=list(dict.fromkeys(assessment.supported_conclusions+[rule]))
        assessment.follow_up_questions=[];assessment.safety_urgency='preventive'
        break
    return assessment
