"""Join input author metadata by ID; never ask the provider to reproduce authors."""
from .schemas import InitialReviewDraft, InitialReview, FinalReviewV6


def bind_draft(draft,request):
    messages={m.id:m for m in request.as_messages()}
    data=draft.model_dump();findings=[];issues=[]
    for index,finding in enumerate(data['findings']):
        ids={e['message_id'] for e in finding['evidence']}
        if not ids<=messages.keys():
            issues.append({'finding_id':finding['id'],'finding_index':index,'errors':['message_id_not_in_original']});continue
        speakers={messages[mid].speaker for mid in ids}
        if len(speakers)!=1:
            issues.append({'finding_id':finding['id'],'finding_index':index,'errors':['finding_spans_multiple_speakers']});continue
        # This is an exact metadata join, not a guessed or repaired model author.
        findings.append({**finding,'speaker':next(iter(speakers))})
    data['findings']=findings
    schema=InitialReview if isinstance(draft,InitialReviewDraft) else FinalReviewV6
    return schema.model_validate(data),issues


def public_evidence_diagnostic(stage,issues,repairs):
    return {'stage':stage,'kind':'evidence','repairs':repairs,
            'issues':[{'finding_index':i.get('finding_index',n),'types':i['errors']} for n,i in enumerate(issues[:12])]}
