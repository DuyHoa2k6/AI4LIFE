"""Backend adjudication for rules + live; no majority vote and no hidden mock fallback."""
from dataclasses import dataclass
from .schemas import Extraction, HybridReview, AnalysisTrace, Answer
from .engine import verify, decide
from .providers import ProviderFailure, unknown
from .mock_rules import VERSION


@dataclass
class HybridBundle:
    preliminary: Extraction | None
    reviewed: HybridReview
    preliminary_risk: str | None
    limited: bool = False


QUESTIONS = {
    'relationship': 'Bạn có biết người gửi và xác nhận đúng người qua kênh liên hệ đã biết từ trước không?',
    'payment_purpose': 'Khoản tiền này dùng để trả khoản đã thỏa thuận, hay là điều kiện để nhận hoặc rút tiền?',
    'channel': 'Thao tác được yêu cầu qua ứng dụng chính thức hay đường dẫn/kênh do người gửi cung cấp?',
    'file_origin': 'Ai gửi tệp và họ yêu cầu bạn mở hoặc cài đặt gì?',
    'permission_purpose': 'Vì sao họ cần chia sẻ màn hình hoặc quyền điều khiển, và bạn đã xác minh đầu mối hỗ trợ chưa?',
    'source_of_request': 'Yêu cầu này do ai đưa ra và có thể xác nhận qua đầu mối độc lập nào?'}


def _overlaps(rule, live):
    return rule.action == live.action and rule.speaker == live.speaker and any(
        a.message_id == b.message_id and max(a.start, b.start) < min(a.end, b.end)
        for a in rule.evidence for b in live.evidence)


def adjudicate(bundle, request):
    original = bundle.reviewed
    valid = verify(original, request.as_messages())
    if original.findings and not valid:
        raise ProviderFailure('EVIDENCE_INVALID', 502)
    by_id = {f.id: f for f in valid}
    review = original.review
    references = set(review.benign_finding_ids + review.uncertain_finding_ids)
    references.update(x for link in review.risk_links for x in (link.request_id, link.support_id))
    invalid_refs = bool(references - by_id.keys())
    context_valid = bool(request.context and review.context_evidence) and all(
        e.end > e.start and e.end <= len(request.context) and
        request.context[e.start:e.end] == e.quote for e in review.context_evidence)
    benign = set(review.benign_finding_ids) & by_id.keys() if context_valid else set()
    # Knowing a sender is not evidence that handing over an authentication code is safe.
    benign = {fid for fid in benign if by_id[fid].action != 'share_auth_code'}
    ungrounded_benign = bool(review.benign_finding_ids and not context_valid)
    uncertain = (set(review.uncertain_finding_ids) & by_id.keys()) | {
        f.id for f in valid if f.speech_role == 'unknown' and f.action != 'inducement'}
    # Claimed benign and risky/uncertain simultaneously must not be treated as settled.
    contradictory = bool(benign & uncertain)
    links = []
    for link in review.risk_links:
        a, b = by_id.get(link.request_id), by_id.get(link.support_id)
        if (a is None or b is None or a.id == b.id or a.action == 'inducement' or
                a.speech_role != 'request' or b.action != 'inducement' or
                b.speech_role not in ('claim', 'request') or a.speaker != b.speaker):
            invalid_refs = True
            continue
        if a.speaker == 'unknown' and {e.message_id for e in a.evidence} != {e.message_id for e in b.evidence}:
            invalid_refs = True
            continue
        if a.id in benign or a.id in uncertain:
            contradictory = True
            continue
        links.append((a, b))
    preliminary = bundle.preliminary.findings if bundle.preliminary is not None else []
    conflicts = [f for f in preliminary if f.speech_role == 'request' and f.action != 'inducement'
                 and not any(_overlaps(f, live) for live in valid)]
    active = [f for f in valid if f.speech_role == 'request' and f.action != 'inducement' and f.id not in benign]
    credential = any(f.action == 'share_auth_code' and f.id not in uncertain for f in active)
    needs_context = (review.needs_context or invalid_refs or ungrounded_benign or contradictory or
                     bool(conflicts or uncertain) or
                     bool(any(f.action == 'transfer_funds' for f in active) and not links and not credential))
    if links or credential:
        status = 'high'
    elif needs_context:
        status = 'need_context'
    elif active:
        status = 'suspicious'
    else:
        status = 'clear'
    # Reuse safe template rendering; none of the provider's free-form answers survives verification.
    extraction = Extraction(answers=original.answers, findings=valid)
    response = decide(extraction, request, 'live')
    response.mode = 'hybrid'
    response.schema_version = '1.1'
    response.risk_status = status
    summaries = {'high': 'Có yêu cầu có thể gây hại dựa trên bằng chứng đã đối chiếu; cần xác minh độc lập.',
                 'need_context': 'Cần thêm bối cảnh hoặc giải quyết bất đồng trước khi kết luận.',
                 'suspicious': 'Có yêu cầu cần xác minh trước khi thực hiện.',
                 'clear': 'Chưa ghi nhận dấu hiệu đáng ngờ trong nội dung và bối cảnh bạn cung cấp; danh tính chưa được xác minh.'}
    response.summary = summaries[status]
    for action, support in links:
        action.inference = Answer(status='inferred',
            text='Live nhận định yêu cầu liên quan tới điều kiện hoặc lời hứa trong các đoạn đã đối chiếu; cần xác minh độc lập.',
            evidence_refs=list(dict.fromkeys([action.id, support.id] + action.inference.evidence_refs)))
    response.findings = valid
    if links:
        response.answers.sequence = Answer(status='inferred', text='Có quan hệ hành vi do live suy luận từ các đoạn đã đối chiếu.',
                                           evidence_refs=list(dict.fromkeys(f.id for pair in links for f in pair)))
    response.answers.evidence_sufficiency = Answer(status='inferred' if valid else 'unknown',
        text=response.summary, evidence_refs=list(by_id))
    response.missing_information = ['Chưa đủ dữ kiện về người gửi, mục đích hoặc điều kiện của yêu cầu.'] if needs_context else []
    topics = list(dict.fromkeys(review.question_topics))
    if needs_context and not topics:
        topics = ['relationship', 'payment_purpose'] if any(f.action == 'transfer_funds' for f in active + conflicts) else ['source_of_request']
    response.follow_up_questions = [QUESTIONS[t] for t in topics[:2]] if needs_context else []
    if benign and not active:
        response.recommended_actions = ['Bối cảnh là thông tin bạn cung cấp; đối chiếu lại người nhận qua đầu mối đã biết nếu có thay đổi.']
    if request.question:
        response.answer_to_user = response.summary + (' ' + ' '.join(response.follow_up_questions) if needs_context else '')
    # Preserve an unresolved rule observation only as unknown, never as an extra vote for high.
    for n, finding in enumerate(conflicts):
        if len(response.findings) >= 50:
            break
        observation = finding.model_copy(deep=True)
        observation.id = f'rule-conflict-{n}'
        while observation.id in by_id:
            observation.id += '-r'
        observation.speech_role = 'unknown'
        observation.description = 'Dấu hiệu từ quy tắc chưa được live giải quyết; cần xác minh thêm'
        observation.inference = unknown()
        response.findings.append(observation)
    response.analysis = AnalysisTrace(rules_version=VERSION,
        preliminary_status='limited' if bundle.limited else 'completed', preliminary_risk=bundle.preliminary_risk,
        preliminary_findings=len(preliminary), rule_conflicts=len(conflicts),
        discarded_live_findings=len(original.findings)-len(valid))
    return response
