"""Bounded, inspectable rules for first-stage observations, never final verdicts."""
import hashlib
import json
from pathlib import Path
import re
import time
from functools import lru_cache

from ..schemas import AnalyzeRequest, Answer, Answers, Finding, Evidence, InitialReview, KEYS
from .schema import Observation, Span, Unit, Participant, Event, Relation, Answers18, AnalysisField, Value
from .text import normalize, units, quote_ranges
from .segmentation import segments
from .abbreviations import resolve
from .syntax import direct_object,speech_scope,transaction_at

RULE_FILE = Path(__file__).with_name('rules.json')
MAX_EVENTS = 50  # Matches the legacy InitialReview finding budget.


@lru_cache(maxsize=1)
def rules():
    data = RULE_FILE.read_bytes()
    config = json.loads(data)
    if config['review_status'] != 'controlled_project_rules' or len(config['rules']) > 64:
        raise ValueError('Invalid local rule configuration')
    ids = [r['id'] for r in config['rules']]
    if len(ids) != len(set(ids)): raise ValueError('Duplicate local rule')
    compiled = [(r, re.compile(r['pattern']), re.compile(r['context']) if r['context'] else None)
                for r in config['rules']]
    return config['version'], hashlib.sha256(data).hexdigest(), compiled


def prune(evidence, events, relations, request, participants=()):
    """Remove invalid evidence, whole dependent events and all dependent relations."""
    messages = {m.id: m for m in request.as_messages()}
    valid = []
    for span in evidence:
        message = messages.get(span.message_id)
        text = message.text if span.source == 'message' and message else request.context if span.source == 'context' else None
        if (text is not None and 0 <= span.start < span.end <= len(text)
                and text[span.start:span.end] == span.quote
                and (span.source == 'context' or span.speaker == message.speaker)):
            valid.append(span)
    ids = {s.id for s in valid}
    events = [e for e in events if set(e.evidence_refs) <= ids and
              {e.verb_span, e.action_span} <= ids and all(x is None or x in ids for x in (e.target_span, e.time_span, e.negation_span))]
    event_ids = {e.action_id for e in events}
    participant_ids={p.id for p in participants}
    relations = [r for r in relations if set(r.evidence_refs) <= ids and
                 r.from_id in event_ids|participant_ids and r.to_id in event_ids|participant_ids]
    return valid, events, relations


def legacy(events, evidence, fields, questions):
    spans = {s.id: s for s in evidence}
    mapping = {'transfer_funds':'transfer_funds', 'provide_credentials':'share_auth_code',
               'share_screen':'grant_access', 'grant_control':'grant_access', 'install_app':'install_app'}
    findings = []
    for event in events:
        span = spans[event.action_span]
        if span.source != 'message': continue
        action = mapping.get(event.action_type, 'other')
        # A bare six-number request is NOT promoted to authentication disclosure.
        if event.action_type == 'provide_code' and re.search(r'\botp\b|ma (?:dang nhap|xac thuc|xac nhan)', normalize(span.quote).text):
            action = 'share_auth_code'
        role = event.speech_role
        if event.polarity == 'negative' and role == 'request': role = 'denial'
        if role == 'reported': role = 'claim'
        findings.append(Finding(id=event.action_id, action=action, description=event.action_type,
            speaker=span.speaker, speech_role=role,
            evidence=[Evidence(message_id=span.message_id, start=span.start, end=span.end, quote=span.quote)],
            inference=Answer(status='unknown', text='Quan sát theo quy tắc; chưa kết luận rủi ro.', evidence_refs=[])))
    old_to_new = dict(zip(KEYS, ('claims','sender_identity','requested_actions','persuasion',
                    'assets_and_access','contradictions_and_alternatives','conditions_and_sequence','evidence_quality')))
    finding_ids = {f.id for f in findings}
    answers = {}
    for key, new_key in old_to_new.items():
        field = fields[new_key]
        refs = [i for i in field.value.event_ids if i in finding_ids]
        status = 'unknown' if not refs else 'observed' if field.status == 'observed' else 'inferred'
        answers[key] = Answer(status=status, text=' '.join(field.value.statements)[:1000] if refs else 'Chưa đủ căn cứ trong quan sát cục bộ.', evidence_refs=refs)
    return InitialReview(answers=Answers(**answers), findings=findings, hypotheses=[], uncertainties=questions)


def analyze(request: AnalyzeRequest) -> Observation:
    started = time.perf_counter()
    version, digest, patterns = rules()
    evidence, events, relations, participants, unit_output, contexts = [], [], [], [], [], {}
    limitations = ['Bộ quy tắc hữu hạn; không chứng minh đủ độ phủ ngôn ngữ hoặc tính xác thực ngoài đời.',
                  'Không kiểm tra mạng URL, không truy xuất RAG, không gọi mô hình, không gán mức cảnh báo cuối.',
                  'Không lưu phiên: khi bổ sung phải gửi lại hội thoại gốc cùng tin mới; không ghép ngầm giữa các request.']
    participant_keys = {}

    def participant(label, role, provenance='text'):
        key = (label, role, provenance)
        if key not in participant_keys:
            pid = 'p' + str(len(participants) + 1)
            participant_keys[key] = pid
            participants.append(Participant(id=pid, label=label, role=role, provenance=provenance))
        return participant_keys[key]

    def span(message, start, end, kind):
        item = Span(id='s' + str(len(evidence) + 1), message_id=message.id, speaker=message.speaker,
                    start=start, end=end, quote=message.text[start:end], kind=kind)
        evidence.append(item)
        return item.id

    for message in request.as_messages():
        speaker = participant(message.speaker, 'speaker', 'metadata')
        quoted_ranges = quote_ranges(message.text)
        current_transaction = None
        for segment in segments(message.text):
            si,sentence_a,sentence_b,a,b,quoted=(segment.sentence_id,segment.context_start,segment.context_end,segment.start,segment.end,segment.quoted)
            text = message.text[a:b]; norm = normalize(text); match_text = norm.text
            sentence = normalize(message.text[sentence_a:sentence_b]).text
            unit_output.append(Unit(message_id=message.id, speaker=message.speaker, sentence_id=f'{message.id}:{si}',
                                    start=a, end=b, quote=text, quoted=quoted,boundary_reason=segment.reason,
                                    boundary_status=segment.status,limitations=segment.limitations))
            tx = re.search(r'\b(?:don|giao dich|hop dong)\s+([a-z0-9]+)\b', match_text)
            if tx and tx.group(1) not in ('hang', 'nay', 'do', 'sau', 'truoc', 'cua', 'da', 'chua'):
                current_transaction = tx.group(0)
            for rule, pattern, context in patterns:
                if context and not context.search(match_text): continue
                for match in pattern.finditer(match_text):
                    kind = rule['type']
                    va, vb = norm.original_range(*match.span('verb')); va += a; vb += a
                    prefix = match_text[:match.start('verb')]
                    if kind=='receive_funds' and re.search(r'\b(?:tai khoan|huong dan|cach)\s*$',prefix):continue
                    if kind=='transfer_funds' and direct_object(match_text[match.end('verb'):]) in ('document','goods','code','credentials'):continue
                    if kind=='receive_funds' and direct_object(match_text[match.end('verb'):])!='money':
                        tx_now=transaction_at(message.text,va)
                        antecedent=bool(re.match(r'\s+du\b',match_text[match.end('verb'):]) and any(
                            e.action_type=='receive_funds' and e.transaction_id==tx_now for e in events))
                        if not antecedent:continue
                    if kind=='login' and re.search(r'(?:huong dan|tai lieu|thong tin)\s*$',prefix):continue
                    # Currency unit "đồng" following an amount is not the verb "đóng".
                    if kind=='transfer_funds' and match.group('verb')=='dong' and re.search(r'\d\s*$',prefix): continue
                    # Merely naming a login code does not mean a login action occurred.
                    if kind == 'login' and re.search(r'ma\s*$', prefix): continue
                    if kind == 'provide_code' and 'mat khau' in match_text: continue
                    neg = list(re.finditer(r'\b(?:dung|cho|khong(?: can| nen| duoc)?|chua(?: duoc)?)\b', prefix))
                    neg=[q for q in neg if q.group() not in ('dung','cho') or text[norm.original_range(*q.span())[0]:norm.original_range(*q.span())[1]].casefold() in ('đừng','dung','chớ')]
                    neg=[q for q in neg if not re.search(r'\bthi\b',prefix[q.end():])]
                    neg_match = neg[-1] if neg and match.start('verb') - neg[-1].end() < 30 else None
                    polarity = 'negative' if neg_match else 'positive'
                    # "đừng gọi" is itself a positive request to avoid verification.
                    if kind in ('avoid_verification', 'keep_secret'): polarity = 'positive'
                    reported = bool(re.search(r'\b(?:ban|ho|nguoi do)\s+(?:noi|bao|nhan|ke)|\b(?:ho|nguoi do)\s+(?:yeu cau)', prefix))
                    quoted_event = any(x <= va < y for x, y in quoted_ranges)
                    if quoted_event:
                        quote_start=max(x for x,y in quoted_ranges if x<=va<y)
                        neg=[m for m in neg if norm.original_range(*m.span())[0]+a>=quote_start]
                        neg_match=neg[-1] if neg and match.start('verb')-neg[-1].end()<30 else None
                        polarity='negative' if neg_match else 'positive'
                    warning = bool(re.search(r'canh bao|canh giac|dung nghe|khong lam theo', sentence))
                    is_state = kind in ('receive_funds','withdraw_funds','identity_claim','relationship_claim','code_identity')
                    completed = bool(re.search(r'\bda\b|vua (?:kiem tra|tu xem)|nhan du', prefix + match_text[match.start():]))
                    pending = bool(neg_match and neg_match.group().startswith('chua')) or bool(re.search(r'cho|bi treo|dang duoc', prefix))
                    if warning and (quoted_event or re.search(r'canh bao|canh giac', sentence)):
                        role = 'quoted_warning'
                    elif reported or quoted_event: role = 'reported'
                    elif is_state or pending or (completed and not re.search(r'\b(?:hay|ban|em|anh|chi)\s*$', prefix)):
                        role = 'claim'
                    elif re.search(r'\b(?:toi|minh)\s+(?:tu\s+)?$', prefix): role = 'claim'
                    else: role = 'request'
                    temporal = 'pending' if pending and role in ('claim','reported') else 'completed' if completed and role in ('claim','reported') else 'requested' if role == 'request' else 'unknown'
                    if re.search(r'\bneu\b', sentence) and role != 'quoted_warning': temporal = 'hypothetical'
                    scope_kind=speech_scope(prefix,sentence)
                    if role not in ('quoted_warning','reported'):
                        if scope_kind in ('not_yet_report','denied_request'):
                            role='claim';polarity='negative';temporal='pending' if scope_kind=='not_yet_report' else 'unknown'
                        elif scope_kind=='conditional_nonperformance':role='claim';polarity='negative';temporal='hypothetical'
                        elif scope_kind=='prohibition':role='request';polarity='negative'
                    actor = None
                    before = normalize(text[:va-a]).text
                    if quoted_event:
                        actor=None  # The reporter's "tôi" is not the quoted actor.
                    elif reported:
                        explicit = re.search(r'\b(ban|ho|nguoi do)\b', before)
                        actor = participant(explicit.group(), 'mentioned') if explicit else None
                    elif re.search(r'\b(?:toi|minh)\b', before): actor = speaker
                    elif role == 'request': actor = participant('người được yêu cầu, chưa rõ danh tính', 'addressee')
                    elif message.speaker != 'unknown': actor = speaker
                    verb_id = span(message, va, vb, 'verb')
                    action_id = span(message, a, b, 'action')
                    target_a = vb
                    while target_a < b and message.text[target_a].isspace(): target_a += 1
                    target_b = b
                    while target_b > target_a and message.text[target_b-1] in '.,!?;”’\" ': target_b -= 1
                    target_id = span(message, target_a, target_b, 'target') if target_a < target_b else None
                    neg_id = None
                    if neg_match:
                        na, nb = norm.original_range(*neg_match.span()); neg_id = span(message, a+na, a+nb, 'negation')
                    time_match = re.search(r'\b(?:hom qua|hom nay|chieu nay|sang nay|ngay mai|trong \d+ phut|truoc \d+ gio)\b', match_text)
                    time_id = None
                    if time_match:
                        ta, tb = norm.original_range(*time_match.span()); time_id = span(message, a+ta, a+tb, 'time')
                    recipient = None
                    destination = re.search(r'\bcho (toi|minh|ben minh|ho|ban)\b', match_text)
                    if destination:
                        label=destination.group(1)
                        recipient=speaker if label in ('toi','minh') and not quoted_event and not reported else participant(label,'addressee' if label=='ban' else 'mentioned')
                    location = re.search(r'\b(?:qua chat|vao chat|tren ung dung|qua zalo|qua telegram)\b', match_text)
                    uncertain_scope = len(neg) > 1 or bool(re.search(r'khong (?:noi|bao)|khong phai', prefix)) or bool(neg and re.search(r'\b(?:va|hoac)\b',prefix[neg[-1].end():]))
                    relative_scope=bool(re.search(r'\b(?:nguoi|ai|don vi)\s+(?:ma\s+)?(?:vua|da|dang)\s*$',prefix))
                    if relative_scope:
                        role='unknown';temporal='unknown';actor=None;uncertain_scope=True
                    if uncertain_scope: polarity='uncertain'
                    event = Event(action_id='a'+str(len(events)+1), action_type=kind,
                        verb_span=verb_id, action_span=action_id, target_span=target_id,
                        negation_span=neg_id, time_span=time_id, actor=actor, recipient=recipient,
                        target=message.text[target_a:target_b] if target_id else None,
                        location=text[norm.original_range(*location.span())[0]:norm.original_range(*location.span())[1]] if location else None,
                        polarity=polarity, speech_role=role, temporal_state=temporal,
                        time_expression=evidence[-1].quote if time_id else None,
                        transaction_id=transaction_at(message.text,va),
                        evidence_refs=[x for x in (verb_id, action_id, target_id, neg_id, time_id) if x],
                        rule_id=rule['id'], limitations=([] if actor else ['Chưa xác định chắc chủ thể của hành động.']) +
                        (['Phạm vi phủ định phức tạp, chưa xác định chắc.'] if uncertain_scope else []))
                    events.append(event)
                    contexts[event.action_id] = (message.id, si, a, sentence, match_text)
                    if len(events) >= MAX_EVENTS: break
                if len(events) >= MAX_EVENTS: break
            if len(events) >= MAX_EVENTS: break
        if len(events) >= MAX_EVENTS:
            limitations.append('Đạt giới hạn 50 hành động; phần còn lại chưa được phân tích, không coi là an toàn.')
            break
    # Regex rules are visited by type; restore document order before linking.
    spans = {s.id:s for s in evidence}
    order = {m.id:i for i,m in enumerate(request.as_messages())}
    events.sort(key=lambda e:(order[spans[e.verb_span].message_id],spans[e.verb_span].start,e.rule_id))

    def connect(kind, left, right, rule_id, status='observed', limits=()):
        if any((r.type,r.from_id,r.to_id)==(kind,left.action_id,right.action_id) for r in relations): return
        relations.append(Relation(relation_id='r'+str(len(relations)+1), type=kind,
            from_id=left.action_id, to_id=right.action_id,
            evidence_refs=list(dict.fromkeys([left.action_span,right.action_span])),
            rule_id=rule_id, status=status, limitations=list(limits)))

    for i, left in enumerate(events):
        for right in events[i+1:]:
            lm, ls, la, sentence, clause = contexts[left.action_id]
            rm, rs, ra, right_sentence, right_clause = contexts[right.action_id]
            if left.transaction_id != right.transaction_id: continue
            same_sentence = lm == rm and ls == rs
            # No cross-message transaction guessing; only explicit code identity reply below.
            same_scope = lm == rm and abs(ls-rs) <= 1
            if not same_scope: continue
            if left.speech_role == 'quoted_warning' or right.speech_role == 'quoted_warning': continue
            if left.action_type == right.action_type and left.polarity != right.polarity:
                if 'hom qua' in clause and 'hom nay' in right_clause:
                    connect('state_update',left,right,'REL-TIMED-UPDATE',limits=['Chỉ là trạng thái do văn bản báo, không xác minh ngân hàng.'])
                elif same_sentence:
                    connect('contradiction',left,right,'REL-OPPOSITE-STATE','inferred', ['Cần xác minh có phải cùng thời điểm/giao dịch không.'])
            pair={left.action_type,right.action_type}
            if pair == {'receive_funds','handover_asset'} and same_sentence:
                if left.polarity == 'negative' and right.polarity == 'negative':
                    connect('prerequisite_for',left,right,'REL-NEGATIVE-CONDITION',limits=['Điều kiện ngăn giao hàng; không phải yêu cầu giao trước khi trả.'])
                elif left.action_type == 'receive_funds' and left.polarity == 'negative' and right.polarity == 'positive' and re.search(r'nhung|truoc',sentence):
                    connect('before',right,left,'REL-HANDOVER-BEFORE-CONFIRMATION',limits=['Thứ tự được yêu cầu; không chứng minh biên lai giả.'])
                elif left.action_type == 'receive_funds' and left.polarity == 'positive' and left.temporal_state == 'completed':
                    connect('before',left,right,'REL-REPORTED-PAYMENT-FIRST',limits=['Trạng thái nhận tiền là lời tự báo.'])
            elif pair == {'receive_funds','handover_asset'} and same_scope and left.action_type=='receive_funds' and left.polarity=='positive' and left.temporal_state=='completed':
                connect('before',left,right,'REL-REPORTED-PAYMENT-FIRST','inferred',
                        ['Hai câu liền nhau có cùng mã giao dịch hoặc chưa nêu mã khác; cần rà nếu có nhiều giao dịch ngầm.'])
            if same_sentence and left.action_type in ('transfer_funds','provide_code','install_app','share_screen','grant_control') and right.action_type in ('receive_funds','withdraw_funds') and re.search(r'\bde\b|\bthi\b|\bmoi\b', right_clause):
                connect('prerequisite_for',left,right,'REL-EXPLICIT-PURPOSE')
                connect('reason_given_for',right,left,'REL-STATED-REASON')
            if same_sentence and left.action_type != right.action_type and re.search(r'\b(?:sau khi|truoc khi|roi|xong)\b', right_clause):
                connect('after' if 'sau khi' in right_clause else 'before',right,left,'REL-EXPLICIT-ORDER')
    codes=[e for e in events if e.action_type=='provide_code' and e.speech_role=='request']
    meanings=[e for e in events if e.action_type=='code_identity']
    if len(codes)==1 and len(meanings)==1:
        connect('state_update', codes[0], meanings[0], 'REL-EXPLICIT-CODE-REPLY','inferred',
                ['Liên kết theo hội thoại gửi lại trong cùng request, không lưu/ghép phiên ngầm.'])
    # Speech annotations connect the reporting speaker to the quoted/reported event.
    for event in events:
        if event.speech_role in ('quoted_warning','reported'):
            author=participant_keys[(spans[event.action_span].speaker,'speaker','metadata')]
            warning=event.speech_role=='quoted_warning'
            relations.append(Relation(relation_id='r'+str(len(relations)+1),
                type='warning_about' if warning else 'reported_by',
                from_id=author if warning else event.action_id,to_id=event.action_id if warning else author,
                evidence_refs=[event.action_span],rule_id='REL-QUOTED-WARNING' if warning else 'REL-REPORTED-SPEECH',
                status='observed',limitations=['Speaker là người thuật lại/cảnh báo, không phải người ra lệnh trong trích dẫn.']))
    evidence, events, relations = prune(evidence, events, relations, request,participants)
    fields, questions = map_fields(request, events, evidence, relations, participants, limitations)
    resolutions=[]
    for message in request.as_messages():
        av,ah,items=resolve(message.text)
        resolutions.extend(dict(item,message_id=message.id,source='message') for item in items)
    if request.context:
        av,ah,items=resolve(request.context)
        resolutions.extend(dict(item,message_id=None,source='context') for item in items)
    uncertain=[r for r in resolutions if r['status']!='resolved']
    if uncertain:
        labels=list(dict.fromkeys(r['quote'] for r in uncertain))[:2]
        questions=([f'“{word}” trong đoạn này có nghĩa là gì? Chỉ giải thích loại thông tin, không gửi mã hoặc mật khẩu thật.' for word in labels]+questions)[:2]
        fields['missing_information'].value.statements=questions
        fields['missing_information'].missing_information=questions
        limitations.append('Có viết tắt thiếu ngữ cảnh hoặc đa nghĩa; giữ nguyên từ đó, không tự chọn nghĩa.')
    result = Observation(rules_version=version, rules_sha256=digest,
        input_sha256=hashlib.sha256(json.dumps(request.model_dump(exclude_none=True),ensure_ascii=False,sort_keys=True).encode()).hexdigest(),
        abbreviation_version=av,abbreviation_sha256=ah,abbreviation_resolutions=resolutions,
        units=unit_output, participants=participants,evidence=evidence,events=events,relations=relations,
        answers_18=Answers18(**fields),follow_up_questions=questions,limitations=limitations,
        adapter=legacy(events,evidence,fields,questions),elapsed_ms=(time.perf_counter()-started)*1000)
    return result


def map_fields(request,events,evidence,relations,participants,limitations):
    spans={s.id:s for s in evidence}
    fields={name:AnalysisField() for name in Answers18.model_fields}

    def fill(name, chosen=(), status='observed', statements=(), rels=(), people=(), extra_refs=()):
        chosen=list(chosen); rels=list(rels)
        refs=list(dict.fromkeys([e.action_span for e in chosen]+[s for r in rels for s in r.evidence_refs]+list(extra_refs)))
        notes=list(statements) or [spans[e.action_span].quote for e in chosen[:4]]
        if chosen or notes or rels or people:
            fields[name]=AnalysisField(status=status,value=Value(statements=notes,event_ids=[e.action_id for e in chosen],
                relation_ids=[r.relation_id for r in rels],participant_ids=list(people)),evidence_refs=refs)
    requests=[e for e in events if e.speech_role=='request' and e.polarity=='positive']
    claims=[e for e in events if e.speech_role in ('claim','reported')]
    fill('situation',events,'inferred', ['Phát hiện các hành động ứng viên trong nội dung; chưa xác định thủ đoạn hoặc tính hợp pháp.'] if events else [])
    fill('participants',status='observed',people=[p.id for p in participants],statements=['Người nói theo metadata; không chứng nhận danh tính thật.'])
    fill('sender_identity',[e for e in events if e.action_type=='identity_claim'],'claimed')
    fill('relationship',[e for e in events if e.action_type=='relationship_claim'],'claimed')
    fill('communication_channel',[e for e in events if e.action_type=='change_channel'])
    fill('claims',claims,'claimed')
    fill('requested_actions',requests)
    fill('action_targets',[e for e in events if e.target or e.actor],'inferred')
    fill('assets_and_access',[e for e in events if e.action_type not in ('identity_claim','relationship_claim','change_channel','keep_secret','avoid_verification')],'inferred')
    fill('conditions_and_sequence',rels=relations)
    fill('contradictions_and_alternatives',[e for e in events if e.polarity=='negative'],rels=[r for r in relations if r.type in ('contradiction','state_update','warning_about')])
    fill('evidence_quality',events,statements=['Quote được cắt từ bản gốc và kiểm tra ID/Unicode offset; không chứng minh nội dung khai báo là thật.'] if events else [])
    purpose_refs=[]; purpose_text=[]; persuasion_refs=[]; persuasion_text=[]
    for message in request.as_messages():
        for _,_,_,a,b,_ in units(message.text):
            n=normalize(message.text[a:b]).text
            purpose=bool(re.match(r'de\b',n))
            persuasion=bool(re.search(r'hoa hong|hoan tien|trong \d+ phut|ngay lap tuc|giu bi mat|neu khong|giu suat',n))
            if purpose or persuasion:
                sid='s'+str(len(evidence)+1)
                evidence.append(Span(id=sid,message_id=message.id,speaker=message.speaker,kind='statement',start=a,end=b,quote=message.text[a:b]))
                if purpose:purpose_refs.append(sid);purpose_text.append(message.text[a:b])
                if persuasion:persuasion_refs.append(sid);persuasion_text.append(message.text[a:b])
    fill('stated_purpose',status='claimed',statements=purpose_text[:4],extra_refs=purpose_refs)
    fill('persuasion',status='claimed',statements=persuasion_text[:4],extra_refs=persuasion_refs)
    # Do not invent beneficiary, personal relationship or technical check results.
    fields['benefit_and_mismatch'].missing_information=['Chưa xác định chắc bên hưởng lợi hoặc sai lệch mục đích; cần rà ngữ nghĩa.']
    fields['technical_checks'].missing_information=['Lượt này chưa chạy kiểm tra kỹ thuật; URL/links đầu vào không phải kết quả xác minh.']
    for name in ('sender_identity','relationship'):
        if fields[name].status!='unknown':fields[name].missing_information=['Chỉ là lời tự nhận, chưa được xác minh độc lập.']
    if request.context:
        sid='s'+str(len(evidence)+1)
        evidence.append(Span(id=sid,source='context',provenance='user_report',message_id=None,speaker=None,kind='statement',start=0,end=len(request.context),quote=request.context))
        fields['claims'].status='claimed'
        fields['claims'].value.statements.append('Bối cảnh người dùng cung cấp (user_report), chưa xác minh: '+request.context)
        fields['claims'].evidence_refs.append(sid)
    questions=[]
    if any(e.polarity=='uncertain' for e in events):
        questions.append('Người gửi đang yêu cầu thực hiện hay ngăn thao tác đó? Hãy cung cấp nguyên văn phần giải thích đã che bí mật.')
    identified=any(e.action_type=='code_identity' for e in events)
    if not identified and any(e.action_type=='provide_code' and e.speech_role=='request' and not re.search(r'otp|ma (?:dang nhap|xac thuc)',normalize(spans[e.action_span].quote).text) for e in events):
        questions.append('Dãy số được thông báo dùng để làm gì? Chỉ mô tả loại mã, không gửi mã thật.')
    if any(e.action_type=='transfer_funds' and e.speech_role=='request' for e in events) and not any(r.type=='prerequisite_for' for r in relations):
        questions.append('Khoản tiền được yêu cầu dùng để thanh toán việc gì?')
    if not events:
        questions.append('Người gửi có yêu cầu bạn thực hiện thao tác cụ thể nào không? Hãy cung cấp đoạn liên quan đã che bí mật.')
        limitations.append('Không phát hiện hành vi thuộc bộ mẫu; không đồng nghĩa nội dung an toàn.')
    if any(e.action_type=='withdraw_funds' and e.temporal_state=='pending' for e in events):
        questions.append('Để tiếp tục rút tiền, họ có yêu cầu chuyển tiền hoặc cung cấp thông tin gì không?')
    questions=list(dict.fromkeys(questions))[:2]
    fill('missing_information',status='unknown',statements=questions)
    fields['missing_information'].missing_information=questions
    fill('assessment',events,'inferred' if events else 'unknown',
         [f'Có {len(events)} hành động ứng viên và {len(relations)} quan hệ theo quy tắc. Chưa kết luận mức rủi ro.',
          'Đối chiếu yêu cầu và kênh thực hiện qua đầu mối độc lập trước khi làm theo.'])
    return fields,questions
