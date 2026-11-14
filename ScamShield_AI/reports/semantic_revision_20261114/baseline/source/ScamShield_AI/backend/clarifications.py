"""Bounded process-local clarification state, optimistic revisions and no model calls."""
from collections import OrderedDict
from dataclasses import dataclass
import hashlib
import json
import re
import threading
import time
import uuid
from .schemas import CaseContext
from .providers import ProviderFailure
from .local_reasoning.clarification_filter import filter_answer
from .local_observation.text import normalize

TTL=900.
LIMIT=100
LOCK=threading.RLock()
CASES=OrderedDict()


def content_version(body):
    data={'messages':[m.model_dump() for m in body.as_messages()],
          'links':[l.model_dump() for l in body.links],'ocr_sources':[s.model_dump() for s in body.ocr_sources]}
    return hashlib.sha256(json.dumps(data,ensure_ascii=False,sort_keys=True).encode()).hexdigest()


def expire():
    now=time.monotonic()
    for key in list(CASES):
        if now-CASES[key]['at']>TTL:del CASES[key]
    while len(CASES)>LIMIT:CASES.popitem(last=False)


@dataclass
class Pending:
    case_id: str
    revision: int
    status: str
    relevant: str
    related_question: bool = False


def prepare(body):
    link=body.clarification
    if link is None:return body,None,None
    with LOCK:
        expire();case=CASES.get(link.case_id)
        if case is None:raise ProviderFailure('CASE_EXPIRED',409)
        meta=case['result'].case_context
        if link.revision!=meta.revision or link.situation_id!=meta.situation_id or link.content_version!=meta.content_version or content_version(body)!=meta.content_version:
            raise ProviderFailure('STALE_ANALYSIS',409)
        if link.question_id not in meta.question_ids:raise ProviderFailure('QUESTION_MISMATCH',422)
        filtered=filter_answer(link.answer)
        if '/transaction:' in meta.situation_id:
            mentions={m.group() for m in re.finditer(r'\b(?:don|giao dich|hop dong)\s+[a-z0-9]+\b',normalize(filtered.relevant_text).text)}
            if mentions and mentions!={meta.situation_id.split('/transaction:',1)[1]}:raise ProviderFailure('SITUATION_MISMATCH',409)
        pending=Pending(link.case_id,meta.revision,filtered.status,filtered.relevant_text,bool(filtered.related_questions))
        if not filtered.relevant_text:return body,pending,case['result'].model_copy(deep=True)
        base=case['body'].model_copy(deep=True)
        # Ignore arbitrary client modifications to context when a versioned
        # clarification is used. Only accepted fragments enter this situation.
        existing=case['context']
        combined='\n'.join(x for x in (existing,filtered.relevant_text) if x)
        if len(combined)>2000 or len(combined.split('\n'))>10:raise ProviderFailure('CONTEXT_TOO_LARGE',422)
        base.context=combined
        base.clarification=link
        return base,pending,None


def finish(body,result,extracted=None,pending=None):
    with LOCK:
        expire()
        if pending:
            case=CASES.get(pending.case_id)
            if case is None or case['result'].case_context.revision!=pending.revision:raise ProviderFailure('STALE_ANALYSIS',409)
            meta=case['result'].case_context.model_copy(deep=True)
            meta.revision+=1;meta.clarification_status=pending.status
            if extracted is not None and extracted.analysis_status=='unsupported':
                meta.clarification_status='unsupported'
                result.input_warnings.append('Thông tin có thể liên quan nhưng ngoài khả năng bóc tách hiện tại; hãy ghi rõ ai yêu cầu làm gì và điều kiện nhận quyền lợi.')
            result.case_context=meta
            if pending.related_question:result.answer_to_user='Theo nội dung đang được kiểm tra, '+result.summary+' '+' '.join(result.recommended_actions[:2])
            if pending.status=='off_topic':
                result.input_warnings.append('Thông tin ngoài phạm vi không được đưa vào tình huống; giữ nguyên đánh giá trước đó.')
            case['context']=body.context if pending.relevant else case['context']
            case['result']=result.model_copy(deep=True);case['at']=time.monotonic()
        else:
            scope='analysis'
            if extracted and extracted.interpretation and extracted.interpretation.situations:
                evidence=set(extracted.assessment.evidence_refs)
                events={e.event_id:e for e in extracted.annotations.events}
                situations=extracted.interpretation.situations
                selected=max(situations,key=lambda s:sum(len(evidence&set(events[e].evidence_refs)) for e in s.event_refs))
                scope=selected.situation_id
            case_id=str(uuid.uuid4())
            result.case_context=CaseContext(case_id=case_id,situation_id=scope,revision=1,content_version=content_version(body),question_ids=['clarify:0'])
            CASES[case_id]={'body':body.model_copy(deep=True),'context':filter_answer(body.context or '').relevant_text,
                            'result':result.model_copy(deep=True),'at':time.monotonic()}
            expire()
        if result.follow_up_questions:
            result.case_context.question_ids=['clarify:'+str(i) for i,_ in enumerate(result.follow_up_questions)]
        else:result.case_context.question_ids=['clarify:0']
        CASES[result.case_context.case_id]['result']=result.model_copy(deep=True)
        if extracted and extracted.interpretation:
            for s in extracted.interpretation.situations:
                if s.situation_id==result.case_context.situation_id:s.version=result.case_context.revision
    return result
