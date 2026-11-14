"""Run local v2 behind the existing AnalyzeRequest/AnalyzeResponse client contract."""
import asyncio
from ..schemas import (AnalyzeResponse,AnalysisTrace,Answer,Answers,Finding,Evidence,RiskIndicator,
                       SourceMatch,RetrievalBranch,RetrievalTrace)
from ..providers import ProviderFailure
from .schema import CaseInput,InputMessage,ContextFact
from .engine import analyze_local


class LocalRulesProvider:
    pipeline='local_rules'

    async def extract(self,request):
        ocr_ids={r.message_id for r in request.ocr_sources}
        originals=request.as_messages();dom=[m for m in originals if m.id not in ocr_ids]
        parent=dom[0].id if len(dom)==1 else None
        messages=[InputMessage(id=m.id,speaker_id=None if m.speaker=='unknown' else m.speaker,text=m.text,
            content_type='ocr' if m.id in ocr_ids else 'text',parent_message_id=parent if m.id in ocr_ids else None,
            scope_id='analysis') for m in originals]
        # OCR may precede DOM in the public message list. Only attach a preceding parent.
        order={m.id:i for i,m in enumerate(messages)}
        for m in messages:
            if m.parent_message_id and order[m.parent_message_id]>=order[m.id]:m.parent_message_id=None
        context=[];context_warnings=[]
        if request.context:
            from .clarification_filter import filter_answer
            filtered=filter_answer(request.context)
            if filtered.relevant_text:
                parts=[s for s in filtered.relevant_text.split('\n') if s.strip()]
                if len(parts)<=10:
                    context=[ContextFact(id='user-context' if len(parts)==1 else 'user-context-'+str(i),text=part,
                        scope_id=request.clarification.situation_id if request.clarification else None,
                        applies_to_message_ids=[m.id for m in messages]) for i,part in enumerate(parts)]
                else:context_warnings.append('Bối cảnh có quá nhiều phần; hãy chia nhỏ để gắn đúng dữ kiện. Chưa dùng bối cảnh này để đổi cảnh báo.')
            if filtered.status in ('off_topic','mixed'):context_warnings.append('Phần bối cảnh ngoài phạm vi được bỏ qua; không dùng nó để thay đổi cảnh báo.')
        result = await asyncio.to_thread(analyze_local,CaseInput(messages=messages,context_facts=context,user_question=request.question))
        result.support_warnings+=context_warnings
        from .support import enrich
        return await enrich(result, request)


def to_public(result,request):
    a=result.assessment
    if a.risk_status is None:
        if result.versions.get('reasoner')=='phobert':
            raise ProviderFailure('PHOBERT_BUSY' if result.versions.get('failure_kind')=='busy' else 'PHOBERT_ANALYSIS_UNAVAILABLE',503,{'stage':'phobert','kind':result.versions.get('failure_kind',result.analysis_status)})
        raise ProviderFailure('LOCAL_ANALYSIS_UNAVAILABLE',503,{'stage':'local_rules','kind':'analysis_error'})
    spans={s.span_id:s for s in result.annotations.spans};messages={m.id:m for m in request.as_messages()}

    def quote(sid):
        s=spans[sid];m=messages.get(s.message_id)
        if not m or not 0<=s.start<s.end<=len(m.text) or m.text[s.start:s.end]!=s.quote:return None
        return Evidence(message_id=m.id,quote=s.quote,start=s.start,end=s.end)

    def checked(ids):
        seen=set();items=[]
        for sid in ids:
            e=quote(sid)
            if e and (e.message_id,e.start,e.end) not in seen:
                seen.add((e.message_id,e.start,e.end));items.append(e)
        return items

    actions={'transfer_funds':'transfer_funds','provide_credentials':'share_auth_code','share_screen':'grant_access',
             'grant_control':'grant_access','install_app':'install_app'}
    findings=[]
    for event in result.annotations.events[:50]:
        evidence=checked(event.evidence_refs)
        if not evidence:continue
        # Do not combine different authors in a public finding.
        author=messages[evidence[0].message_id].speaker
        evidence=[e for e in evidence if messages[e.message_id].speaker==author]
        action=actions.get(event.event_type,'other')
        if event.event_type=='provide_code':
            from ..local_observation.text import normalize
            if any(t in normalize(evidence[0].quote).text for t in ('otp','ma dang nhap','ma xac thuc')):action='share_auth_code'
        role=event.speech_role
        # Public Finding has five roles; keep finer attribution in raw Event.
        # A report is a claim, never the user's own direct request.
        if role in ('hypothetical','reported'):role='claim'
        findings.append(Finding(id=event.event_id,action=action,description=event.description,speaker=author,
            speech_role=role,evidence=evidence,inference=Answer(status='unknown',text='Quan sát theo quy tắc, chưa xác minh sự việc ngoài đời.',evidence_refs=[])))
    mapping={'claim':'claims','claimed_identity':'sender_identity','requested_action':'requested_actions','persuasion':'persuasion',
             'assets_at_risk':'assets_and_access','impersonation':'contradictions_and_alternatives','sequence':'conditions_and_sequence','evidence_sufficiency':'evidence_quality'}
    ids={f.id for f in findings};answers={}
    for old,new in mapping.items():
        field=getattr(result.annotations.answers_18,new)
        refs=[i for i in field.value.event_ids if i in ids]
        answers[old]=Answer(status='unknown' if not refs else 'observed' if field.status=='observed' else 'inferred',
            text=' '.join(field.value.statements)[:1000] if refs else 'Chưa đủ căn cứ trong phần đã phân tích.',evidence_refs=refs)
    basis=checked(a.evidence_refs);urgent_basis=checked(a.urgency_evidence_refs)
    context_indicators=[]
    if a.risk_status in ('suspicious','high'):
        for frame in result.interaction_frames:
            if frame.speech_role!='request' or not frame.condition or not set(frame.evidence_refs)&set(a.evidence_refs):continue
            evidence=checked(frame.evidence_refs)
            if evidence:context_indicators.append(RiskIndicator(kind='interaction_context',evidence=evidence,
                explanation='Người gửi đặt yêu cầu với người nhận: '+frame.condition+' '+frame.possible_effect))
    source_status=result.knowledge_status if result.knowledge_status in ('disabled','no_approved_sources','no_match','matched','timeout','error') else 'disabled'
    trace=AnalysisTrace(pipeline='local_rules',routing='local_backend',rules_version=result.versions.get('rulebook','unknown'),
        preliminary_status='completed' if result.analysis_status=='complete' else 'limited',preliminary_risk=result.versions.get('text_risk_status',a.risk_status),preliminary_findings=len(result.annotations.events),
        rule_conflicts=len(result.fact_trace.conflicts) if result.fact_trace else 0,discarded_live_findings=0,live_status='not_used',
        decision_version='facts-1.0-support' if result.fact_trace else 'local-situation-1.0-support' if result.versions.get('interpretation')=='local-situation-1.0' else 'context-1.0-support' if result.versions.get('context')=='interaction-context-1.0' else 'local-rules-2.1-support',
        situation_facts=len(result.annotations.events),situation_links=len(result.annotations.relations),
        information_needed=bool(a.follow_up_questions),stage_timings_ms={'local_total':result.elapsed_ms,**result.core_timings_ms,**result.support_timings_ms},
        used_url_evidence=len(result.url_uses))
    if result.versions.get('reasoner')=='phobert':trace.decision_version='phobert-structured-1.0-support'
    return AnalyzeResponse(schema_version='2.0',mode='local_rules',risk_status=a.risk_status,summary=a.summary,
        answers=Answers(**answers),findings=findings,missing_information=a.missing_information,follow_up_questions=a.follow_up_questions,
        recommended_actions=a.recommended_actions,answer_to_user=(a.summary if any(t in request.question.casefold() for t in ('rủi ro','lừa đảo','xác minh','làm gì','nguy hiểm','an toàn','cảnh báo')) else 'Bộ phân tích cục bộ chỉ hỗ trợ đánh giá yêu cầu, dấu hiệu rủi ro và cách xác minh; câu hỏi này nằm ngoài phạm vi xử lý.') if request.question else None,
        source_matches=[SourceMatch(source_id=s.source_id,url=s.url,quote=s.quote,match_level='behavior_support' if s.relation=='behavior_support' else 'background',reviewed_at=s.reviewed_at,valid_until=s.valid_until) for s in result.source_matches],
        analysis=trace,retrieval=RetrievalTrace(scenarios=RetrievalBranch(status='disabled',retrieved_count=0,elapsed_ms=0.),
            official_sources=result.official_retrieval or RetrievalBranch(status=source_status,retrieved_count=len(result.source_matches),elapsed_ms=0.)),
        display_summary=a.summary[:600],display_action=a.recommended_actions[0][:600] if a.recommended_actions else None,
        risk_indicators=([RiskIndicator(kind='local_rule_basis',evidence=basis,explanation=a.summary)] if basis else [])+context_indicators+result.support_indicators,
        url_analysis=result.url_analysis,url_uses=result.url_uses,
        safety_urgency=a.safety_urgency,urgency_evidence=urgent_basis,analysis_status=result.analysis_status,
        input_warnings=[('Phân tích bằng PhoBERT cục bộ và quy tắc trên cấu trúc dự đoán; chưa xác minh danh tính ngoài đời.' if result.versions.get('reasoner')=='phobert' else 'Phân tích cục bộ theo quy tắc có phạm vi giới hạn; không xác minh danh tính ngoài đời.')]+result.support_warnings+
            (['Phân tích chưa hoàn tất; giữ tín hiệu an toàn còn có căn cứ.'] if result.analysis_status in ('partial','error') else []))
