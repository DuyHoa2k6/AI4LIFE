"""Join grounded events with bounded approved retrieval and URL observations; no model."""
import asyncio
import time
from .. import retrieval
from ..schemas import Evidence, RiskIndicator, UrlUse, RetrievalBranch
from ..settings import get_setting, LocalConfigError
from ..urls import collect, STRONG
from ..url_network import inspect_urls
from ..local_observation.segmentation import segments
from ..local_observation.text import normalize
from .schema import SourceSupport

# Technical signals need a live request linked to the URL, never a mere mention.
URL_ACTIONS={'open_link','login','provide_code','provide_credentials','provide_documents',
             'transfer_funds','install_app','share_screen','grant_control'}
ALIASES={'provide_credentials':{'share_auth_code'},'provide_code':{'share_auth_code'},
         'share_screen':{'grant_access'},'grant_control':{'grant_access'}}


def event_evidence(result,request,event):
    messages={m.id:m.text for m in request.as_messages()};spans={s.span_id:s for s in result.annotations.spans}
    evidence=[]
    for sid in event.evidence_refs:
        s=spans.get(sid);text=messages.get(s.message_id) if s else None
        if text is not None and 0<=s.start<s.end<=len(text) and text[s.start:s.end]==s.quote:
            evidence.append(Evidence(message_id=s.message_id,start=s.start,end=s.end,quote=s.quote))
    return evidence


def active_requests(result,request):
    return [(e,event_evidence(result,request,e)) for e in result.annotations.events[:50]
            if e.speech_role=='request' and e.polarity=='positive' and e.status!='unknown'
            and e.temporal_state not in ('past','hypothetical')]


def linked_evidence(request,record,evidence):
    """Require a unique grounded label/URL and action within one clause."""
    message=next((m for m in request.as_messages() if m.id==record['message_id']),None)
    if not message:return []
    label=record.get('display_text') or record['url'];start=record.get('start')
    if start is None:
        if message.text.count(label)!=1:return []
        start=message.text.index(label)
    if message.text[start:start+len(label)]!=label:return []
    end=start+len(label)
    for e in evidence:
        if e.message_id!=message.id:continue
        # DOM text extraction separates adjacent text nodes with newlines. An
        # explicit href immediately after a linking preposition is still grounded;
        # do not extend this to unrelated sentences, speakers or bare pasted URLs.
        if record.get('origin')=='dom_href' and 0<=start-e.end<=120:
            gap=normalize(message.text[e.end:start]).text.strip()
            if gap in ('tai','qua','vao','theo','tai lien ket','qua lien ket','theo duong dan'):
                return [e,Evidence(message_id=message.id,start=start,end=end,quote=label)]
        for segment in segments(message.text):
            if segment.quoted or segment.status=='uncertain':continue
            if segment.start<=min(e.start,start) and max(e.end,end)<=segment.end:
                return [e,Evidence(message_id=message.id,start=start,end=end,quote=label)]
    return []


async def enrich(result,request):
    started=time.perf_counter()
    result.versions['text_risk_status']=result.assessment.risk_status or 'unavailable'
    result.versions['support']='local-support-1.0'
    result.source_matches=[]  # Never expose unconsumed hits from an earlier stage.
    if result.assessment.safety_urgency=='urgent' or result.analysis_status=='error':
        result.knowledge_status='not_checked_urgent' if result.assessment.safety_urgency=='urgent' else 'not_checked'
        result.support_warnings.append('Ưu tiên tín hiệu an toàn; chưa đối chiếu nguồn và URL.')
        return result
    requests=[(e,ev) for e,ev in active_requests(result,request) if ev]
    query='\n'.join(dict.fromkeys(x.quote for _,ev in requests for x in ev))
    actions=sorted({a for e,_ in requests for a in ({e.event_type}|ALIASES.get(e.event_type,set()))})
    try:timeout=float(get_setting('SCAMSHIELD_RETRIEVAL_TIMEOUT','.8'))
    except (TypeError,ValueError):raise LocalConfigError('Invalid retrieval timeout') from None
    timeout=max(.01,min(timeout,2.))
    records={r['id']:r for r in collect(request)}

    async def sources():
        if not query:
            return RetrievalBranch(status='no_match',retrieved_count=0,elapsed_ms=0.),[]
        return await retrieval.branch('official_sources',query,actions,
            enabled=get_setting('SCAMSHIELD_RAG_ENABLED','1')=='1',timeout=timeout)

    async def urls():
        if not records:
            return [],0.
        t=time.perf_counter()
        try:
            value=await inspect_urls(request,network=True)
        except (OSError,ValueError,TimeoutError):
            from ..urls import analyze_urls
            value=analyze_urls(request)
            for item in value:item.network.status='error';item.network.reason='inspection_failed'
        return value,(time.perf_counter()-t)*1000

    (trace,hits),(analyses,url_ms)=await asyncio.gather(sources(),urls())
    result.official_retrieval=trace;result.knowledge_status=trace.status
    result.url_analysis=analyses
    technical=result.annotations.answers_18.technical_checks
    url_spans=[s.span_id for s in result.annotations.spans if s.label=='url' and any(u.message_id==s.message_id for u in analyses)]
    if analyses and url_spans:
        technical.status='observed';technical.extraction_method='local_url_checks';technical.rule_ids=['URL-STRUCTURE-HEAD']
        technical.evidence_refs=url_spans
        technical.value.statements=['URL '+(u.hostname or 'không hợp lệ')+': trạng thái mạng '+u.network.status+'; chưa kiểm tra danh tiếng hoặc nội dung trang.' for u in analyses]
    result.support_timings_ms={'retrieval':trace.elapsed_ms,'url':url_ms}
    for link in analyses:
        codes=sorted({s.code for s in link.signals}&STRONG)
        record=records.get(link.link_id)
        if not codes or record is None:continue
        for event,evidence in requests:
            if event.event_type not in URL_ACTIONS:continue
            basis=linked_evidence(request,record,evidence)
            if not basis:continue
            result.url_uses.append(UrlUse(link_id=link.link_id,signal_codes=codes,
                finding_refs=[event.event_id],relation='supports_request_risk'))
            explanation='Yêu cầu trong nội dung gắn với liên kết có dấu hiệu tên miền cần xác minh: '+ '; '.join(s.detail for s in link.signals if s.code in codes)
            result.support_indicators.append(RiskIndicator(kind='url_support',evidence=basis,explanation=explanation))
            if result.assessment.risk_status in ('clear','need_context'):
                result.assessment.risk_status='suspicious'
                result.assessment.summary='Có yêu cầu thực hiện qua liên kết có dấu hiệu tên miền đáng ngờ; cần xác minh trước khi làm theo.'
                result.assessment.safety_urgency='preventive'
                result.assessment.applicable_rule_ids.append('R-URL-GROUNDED-REQUEST')
            action='Không làm theo liên kết chưa xác minh; tự mở ứng dụng hoặc địa chỉ chính thức đã biết để kiểm tra.'
            if action not in result.assessment.recommended_actions:result.assessment.recommended_actions.insert(0,action)
            break
    for hit in hits:
        # Approved search gates metadata; second gate binds a behavior-support passage
        # to observed request types. Background/candidate hits never change the verdict.
        if hit.get('source_role')!='behavior_support':continue
        matches=[(e,ev) for e,ev in requests if ({e.event_type}|ALIASES.get(e.event_type,set()))&set(hit.get('actions',[]))
                 and len(retrieval.tokens(' '.join(x.quote for x in ev))&retrieval.tokens(hit['text']))>=2]
        if not matches or result.assessment.risk_status not in ('suspicious','high'):continue
        result.source_matches.append(SourceSupport(source_id=hit['id'],url=hit['url'],quote=hit['text'],
            relation='behavior_support',event_refs=[e.event_id for e,_ in matches],
            reviewed_at=hit['reviewed_at'],valid_until=hit.get('valid_until')))
        result.support_indicators.append(RiskIndicator(kind='official_behavior_support',
            evidence=matches[0][1],explanation='Yêu cầu đã trích có hành vi tương ứng với tài liệu chính thống đã duyệt; điều này không xác minh danh tính hoặc chứng minh vụ việc.'))
    if result.source_matches:
        action='Đối chiếu yêu cầu qua đầu mối chính thức độc lập; không dùng thông tin liên hệ do người gửi tự cung cấp.'
        if action not in result.assessment.recommended_actions:result.assessment.recommended_actions.append(action)
    if trace.status in ('timeout','error','no_approved_sources'):
        result.support_warnings.append({'timeout':'Truy xuất tài liệu quá thời gian; giữ kết quả có bằng chứng từ nội dung.',
            'error':'Chưa đối chiếu được tài liệu; giữ kết quả có bằng chứng từ nội dung.',
            'no_approved_sources':'Kho chưa có nguồn chính thống được duyệt; không dùng nguồn candidate.'}[trace.status])
    if any(a.network.status in ('error','timeout','blocked','unsupported','deferred','redirect_limit','redirect_loop') for a in analyses):
        result.support_warnings.append('Một số liên kết chưa kiểm tra mạng đầy đủ; lỗi, bị chặn hoặc không truy cập được không tự chứng minh lừa đảo.')
    result.support_timings_ms['support_total']=(time.perf_counter()-started)*1000
    # Keep the 18-field assessment consistent with the enriched final decision.
    result.annotations.answers_18.assessment.value.statements=[result.assessment.summary]
    from .support_facts import attach
    attach(result)
    return result
