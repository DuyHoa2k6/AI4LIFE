import re
from .schemas import Answer, Answers, AnalyzeResponse, KEYS
from .providers import ProviderFailure, unknown
from .mock_rules import assess as assess_mock

DESCRIPTIONS = {'transfer_funds': 'Yêu cầu chuyển hoặc ứng tiền',
                'share_auth_code': 'Yêu cầu cung cấp mã đăng nhập hoặc xác thực',
                'grant_access': 'Yêu cầu chia sẻ màn hình hoặc quyền điều khiển',
                'install_app': 'Yêu cầu cài phần mềm', 'other': 'Hành động cần xác minh',
                'inducement': 'Lời hứa hoặc điều kiện cần đối chiếu'}


def verify(extraction, messages):
    by_id = {m.id: m for m in messages}
    counts = {}
    for f in extraction.findings:
        counts[f.id] = counts.get(f.id, 0) + 1
    valid = []
    for raw in extraction.findings:
        if counts[raw.id] != 1:
            continue
        f = raw.model_copy(deep=True)
        evidence = []
        for ev in f.evidence:
            msg = by_id.get(ev.message_id)
            if msg is None or f.speaker != msg.speaker:
                continue
            if ev.start is None and ev.end is None:
                positions = [m.start() for m in re.finditer('(?=' + re.escape(ev.quote) + ')', msg.text)]
                if len(positions) != 1:
                    continue
                ev.start, ev.end = positions[0], positions[0] + len(ev.quote)
            if (ev.start is None or ev.end is None or ev.end <= ev.start or
                    ev.end > len(msg.text) or msg.text[ev.start:ev.end] != ev.quote):
                continue
            evidence.append(ev)
        # Partial evidence may alter the meaning of an extracted finding: discard it all.
        if len(evidence) != len(f.evidence):
            continue
        f.evidence = evidence
        f.description = DESCRIPTIONS[f.action]
        f.inference = unknown()
        valid.append(f)
    return valid


def decide(extraction, request, mode):
    findings = verify(extraction, request.as_messages())
    if extraction.findings and not findings:
        raise ProviderFailure('EVIDENCE_INVALID', 502)
    requests = [f for f in findings if f.speech_role == 'request' and f.action != 'inducement']
    supporting = [f for f in findings if f.action == 'inducement' and f.speech_role in ('request', 'claim')]
    # Context contributes only through verified findings, never arbitrary model prose.
    high = bool(requests and (supporting or any(f.action == 'share_auth_code' for f in requests)))
    text = '\n'.join(m.text for m in request.as_messages()).lower()
    missing = []
    questions = []
    links = []
    if mode == 'mock':
        status, links, questions = assess_mock(findings, request.as_messages())
        if questions:
            missing = ['Chưa rõ mục đích, vai trò hoặc điều kiện của yêu cầu.']
        for action, support in links:
            action.inference = Answer(status='inferred',
                text='Yêu cầu có thể liên quan tới điều kiện nhận/rút tiền hoặc lời hứa trong các bằng chứng này.',
                evidence_refs=list(dict.fromkeys([action.id, support.id] + action.inference.evidence_refs)))
    elif high:
        status = 'high'
    elif requests:
        status = 'suspicious'
    elif not findings and any(s in text for s in ['bị treo', 'xác minh tài khoản', 'gửi một tệp', 'gửi tệp']):
        status = 'need_context'
        missing = ['Chưa rõ thao tác được yêu cầu và kênh thực hiện.']
        questions = ['Người gửi yêu cầu bạn thực hiện thao tác gì và qua kênh nào?']
        if 'bị treo' in text:
            questions = ['Họ có yêu cầu chuyển tiền để mở khóa khoản rút không?']
    else:
        status = 'clear'
    summaries = {'high': 'Có yêu cầu có thể gây hại trong nội dung đã cung cấp.',
                 'suspicious': 'Có yêu cầu cần xác minh trước khi thực hiện.',
                 'need_context': 'Cần thêm bối cảnh để đánh giá.',
                 'clear': 'Chưa ghi nhận yêu cầu đáng ngờ trong phần đã kiểm tra.'}
    answers = {key: unknown() for key in KEYS}
    if requests:
        descriptions = '; '.join(dict.fromkeys(f.description for f in requests))
        answers['requested_action'] = Answer(status='observed', text=descriptions,
                                            evidence_refs=[f.id for f in requests])
        answers['assets_at_risk'] = Answer(status='inferred', text='Nếu thực hiện, tiền, dữ liệu hoặc quyền truy cập có thể bị ảnh hưởng.',
                                          evidence_refs=[f.id for f in requests])
    if supporting:
        answers['persuasion'] = Answer(status='observed', text='Có lời hứa hoặc điều kiện do người gửi nêu; chưa được xác minh.',
                                      evidence_refs=[f.id for f in supporting])
        answers['claim'] = Answer(status='observed',
            text='Người nói nêu lời hứa hoặc điều kiện trong các đoạn trích; nội dung tuyên bố chưa được xác minh.',
            evidence_refs=[f.id for f in supporting])
    if links:
        answers['sequence'] = Answer(status='inferred',
            text='Trong phạm vi cửa sổ quy tắc, yêu cầu và lời hứa/điều kiện liên quan xuất phát từ cùng người nói; quan hệ này chưa được AI live xác minh.',
            evidence_refs=list(dict.fromkeys(f.id for pair in links for f in pair)))
    answers['evidence_sufficiency'] = Answer(status='inferred' if findings else 'unknown',
        text=summaries[status], evidence_refs=[f.id for f in findings])
    recommendations = ['Xác minh qua đầu mối độc lập do bạn tự tìm; không cung cấp mã hoặc chuyển tiền khi chưa rõ.'] if requests else []
    actions = {f.action for f in requests}
    if 'transfer_funds' in actions:
        recommendations.append('Đối chiếu yêu cầu thanh toán và người nhận qua đầu mối đã biết; không nộp thêm chỉ để mở khóa khoản rút.')
    if actions & {'grant_access', 'install_app'}:
        recommendations.append('Xác minh đơn vị hỗ trợ qua kênh độc lập trước khi cài phần mềm hoặc cấp quyền điều khiển.')
    user_answer = None
    if request.question:
        user_answer = (answers['requested_action'].text + '. ' + answers['assets_at_risk'].text
                       if requests else 'Chưa đủ bằng chứng để trả lời câu hỏi cụ thể. ' + summaries[status])
    return AnalyzeResponse(mode=mode, risk_status=status, summary=summaries[status],
        answers=Answers(**answers), findings=findings, missing_information=missing,
        follow_up_questions=questions, recommended_actions=recommendations, answer_to_user=user_answer)
