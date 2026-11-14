"""Ground relation assertions; lexical cues request review, never establish high."""
import re
from .engine import verify


CONDITION = re.compile(
    r'chỉ\s+(?:khi|sau khi)|(?:thiếu|không có).{0,100}thì|'
    r'(?:đủ|có).{0,80}thì.{0,80}mới|điều kiện|bắt buộc|'
    r'(?:chuyển|nộp|gửi|cài|cấp).{0,100}trước.{0,100}(?:nhận|hoàn|rút)', re.I)


def eligible(a, b):
    return (a.id != b.id and a.action != 'inducement' and a.speech_role == 'request'
            and b.action == 'inducement' and b.speech_role in ('request', 'claim')
            and a.speaker == b.speaker
            and (a.speaker != 'unknown' or
                 {e.message_id for e in a.evidence} == {e.message_id for e in b.evidence}))


def evidence_feedback(reviewed, request):
    """Concrete private repair facts, without suggesting a risk verdict or editing quotes."""
    valid = {f.id for f in verify(reviewed, request.as_messages())}
    messages = {m.id:m for m in request.as_messages()}
    feedback = []
    for finding_index,finding in enumerate(reviewed.findings):
        if finding.id in valid:
            continue
        errors = set()
        for ev in finding.evidence:
            msg = messages.get(ev.message_id)
            if msg is None:
                errors.add('message_id_not_in_original')
                continue
            if finding.speaker != msg.speaker:
                errors.add('speaker_metadata_mismatch')
            if ev.quote not in msg.text:
                errors.add('quote_not_verbatim')
            elif ev.start is None and ev.end is None and msg.text.count(ev.quote) != 1:
                errors.add('quote_ambiguous_without_offsets')
            elif (ev.start is not None or ev.end is not None) and (
                    ev.start is None or ev.end is None or msg.text[ev.start:ev.end] != ev.quote):
                errors.add('quote_offsets_mismatch')
        feedback.append({'finding_id':finding.id,'finding_index':finding_index, 'errors':sorted(errors) or ['duplicate_or_invalid_finding'],
                         'instruction':'Re-copy a contiguous verbatim substring from input, or separate '
                         'disjoint passages into evidence entries. Never join them with [...] or rewrite '
                         'characters. Keep the original message speaker metadata. Reassess links only '
                         'after evidence is valid; these facts do not establish a risk level.'})
        if len(feedback) == 12:
            break
    return feedback


def inspect_relations(reviewed, request, message_benign_ids=None):
    """Return hard validation issues and bounded omission hints based on verified input.

    Finding quote verification is reused for Unicode, duplicates and speaker checks.
    Notes/missing explanations are model judgements, not proven semantic facts.
    """
    findings = {f.id:f for f in verify(reviewed, request.as_messages())}
    messages = {m.id:m for m in request.as_messages()}
    links = {(x.request_id, x.support_id) for x in reviewed.review.risk_links}
    unresolved = {(x.request_id, x.support_id) for x in reviewed.uncertain_relations}
    assessments, issues = {}, set()
    for relation in reviewed.relation_assessments:
        pair = relation.request_id, relation.support_id
        if pair in assessments:
            issues.add('duplicate_relation_assessment')
        assessments[pair] = relation
        a, b = (findings.get(fid) for fid in pair)
        if (a is None or b is None or a.id == b.id or
                (relation.status != 'not_supporting_risk' and not eligible(a, b))):
            issues.add('relation_endpoint_unverified')
            continue
        if not relation.relation_evidence:
            issues.add('relation_evidence_missing')
        else:
            endpoint_spans = a.evidence + b.evidence
            for ev in relation.relation_evidence:
                msg = messages.get(ev.message_id)
                if msg is None:
                    issues.add('relation_evidence_invalid')
                    continue
                probe = a.model_copy(update={'speaker':msg.speaker, 'evidence':[ev]},deep=True)
                grounded = verify(reviewed.model_copy(update={'findings':[probe]}), request.as_messages())
                if not grounded or not any(e.message_id == f.message_id
                        and max(e.start, f.start) < min(e.end, f.end) for e in grounded[0].evidence
                        for f in endpoint_spans):
                    issues.add('relation_evidence_invalid')
        if relation.status == 'supported':
            if pair not in links or pair in unresolved:
                issues.add('supported_relation_without_risk_link')
            if relation.relation_type in ('ordinary_transaction','unrelated','unknown'):
                issues.add('unsupported_risk_relation_type')
            if relation.unresolved_reference or relation.missing_information:
                issues.add('supported_relation_has_missing_basis')
        elif relation.status == 'uncertain':
            if pair not in unresolved or pair in links:
                issues.add('uncertain_assessment_without_uncertain_pair')
            gap = (relation.missing_information or '').strip().casefold().rstrip('.?!')
            if not gap or gap in {'chưa rõ','chưa đủ thông tin','cần thêm thông tin',
                                  'chưa xác minh danh tính','chưa biết có lừa đảo'}:
                issues.add('uncertain_relation_missing_specific_gap')
        elif pair in links or pair in unresolved:
            issues.add('rejected_relation_still_linked')
    for pair in links | unresolved:
        if pair not in assessments:
            issues.add('relation_assessment_missing')

    # Exempt only context-grounded benign requests. A name or keyword alone is no cue.
    context_valid = bool(request.context and reviewed.review.context_evidence) and all(
        0 <= e.start < e.end <= len(request.context) and request.context[e.start:e.end] == e.quote
        for e in reviewed.review.context_evidence)
    benign = (set(reviewed.review.benign_finding_ids) if context_valid else set())|set(message_benign_ids or set())
    hints = []
    for a in findings.values():
        if a.action not in ('transfer_funds','grant_access','install_app','other') or a.id in benign:
            continue
        for b in findings.values():
            pair = a.id, b.id
            if pair in links or not eligible(a, b):
                continue
            # Inspect only short input spans around both endpoints; ignore unrelated DOM/context.
            ids = {e.message_id for f in (a,b) for e in f.evidence}
            spans = []
            for mid in ids:
                ev = [e for f in (a,b) for e in f.evidence if e.message_id == mid]
                start, end = min(e.start for e in ev), max(e.end for e in ev)
                if end-start > 700:
                    continue
                spans.append(messages[mid].text[start:end])
            if CONDITION.search('\n'.join(spans)):
                hints.append({'request_id':a.id, 'support_id':b.id,
                              'cue':'possible_prerequisite_in_original'})
            if len(hints) >= 12:
                return sorted(issues), hints
    return sorted(issues), hints
