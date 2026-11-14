"""Check semantic relationships between fields without inventing a risk verdict."""


def review_issues(reviewed):
    findings = {f.id: f for f in reviewed.findings}
    issues = set()
    if len(findings) != len(reviewed.findings):
        issues.add('duplicate_finding_id')
    review = reviewed.review
    reasons = {}
    for reason in reviewed.uncertainty_reasons:
        if reason.finding_id not in findings:
            issues.add('unknown_uncertainty_ref')
        reasons.setdefault(reason.finding_id, set()).add(reason.kind)
    uncertain = set(review.uncertain_finding_ids)
    benign = set(review.benign_finding_ids)
    blocking = {fid for fid, kinds in reasons.items() if kinds & {'action', 'relation'}}
    blocking |= {fid for fid in uncertain if not reasons.get(fid)}
    if (uncertain | benign) - findings.keys():
        issues.add('unknown_review_ref')
    if benign & (uncertain | blocking):
        issues.add('benign_and_uncertain')
    if any(findings[fid].action == 'share_auth_code' for fid in benign & findings.keys()):
        issues.add('auth_code_cannot_be_benign')
    unresolved = {(x.request_id, x.support_id) for x in reviewed.uncertain_relations}
    links = {(x.request_id, x.support_id) for x in review.risk_links}
    if unresolved & links:
        issues.add('relation_both_asserted_and_uncertain')
    for request_id, support_id in links | unresolved:
        a, b = findings.get(request_id), findings.get(support_id)
        if (a is None or b is None or a.id == b.id or a.action == 'inducement'
                or a.speech_role != 'request' or b.action != 'inducement'
                or b.speech_role not in ('request', 'claim') or a.speaker != b.speaker
                or (a.speaker == 'unknown' and
                    {e.message_id for e in a.evidence} != {e.message_id for e in b.evidence})):
            issues.add('invalid_relation_endpoints')
    for a, b in links:
        if {a, b} & benign:
            issues.add('risk_link_and_benign')
        if {a, b} & blocking:
            issues.add('risk_link_and_blocking_uncertainty')
    if unresolved and not review.needs_context:
        issues.add('uncertain_relation_requires_context')
    return sorted(issues)
