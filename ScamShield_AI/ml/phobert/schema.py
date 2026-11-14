"""Independent supervised contract. Offsets always index original Python strings."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

VERSION='phobert-structured-1.0'
SPAN_LABELS=['entity','action','object','condition','purpose','time','negation','benefit','consequence']
ATTRS={
 'action_type':['none','transfer','receive','disclose_credentials','login','handover','grant_control','share_screen','install','borrow','retain_documents','restrict_exit','threaten_disclosure','avoid_verification','verify','misstate_origin','withdraw','other'],
 'object_type':['unknown','money','document','auth_code','credentials','goods','device','financial_data','identity_document','movement','information'],
 'speech_act':['request','claim','reported','quoted_warning','prohibition','hypothetical','unknown'],
 'polarity':['positive','negative','uncertain'],
 'temporal_state':['requested','completed','not_completed','pending','ongoing','future','unknown'],
 'modality':['assertion','request','conditional','promise','threat','possibility','unknown'],
}
ROLES=['speaker','requester','performer','recipient','affected_party','transfer_source','transfer_destination']
# same_transaction is symmetric; all other labels are directed. Multiple labels may coexist.
RELATIONS=['same_transaction','before','after','prerequisite_for','promised_after','threatens_unless','contradiction','state_update','obstructs_verification','transfer_via','controls_during']
RISKS=['clear','need_context','suspicious','high']

class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid')
class Message(Strict):
    id:str=Field(min_length=1,max_length=100)
    speaker_id:str|None=Field(default=None,min_length=1,max_length=100)
    text:str=Field(min_length=1,max_length=10000)
class Span(Strict):
    id:str
    message_id:str
    start:int=Field(ge=0)
    end:int=Field(gt=0)
    quote:str
    label:str
class Participant(Strict):
    id:str
    kind:Literal['metadata','mention','unknown']
    speaker_id:str|None=None
    span_id:str|None=None
class Event(Strict):
    id:str
    anchor_id:str
    attributes:dict[str,str|None]
    transaction_id:str|None=None
class Argument(Strict):
    event_id:str
    role:str
    participant_id:str
class Relation(Strict):
    source:str
    target:str
    label:str
    evidence_refs:list[str]=Field(min_length=1)
class Sample(Strict):
    schema_version:Literal['phobert-structured-1.0']=VERSION
    id:str
    family_id:str
    conversation_group:str
    template_group:str
    source_group:str
    source:Literal['synthetic','consented_real','public_regression']
    review_status:Literal['draft','independently_reviewed','adjudicated']
    reviewers:list[str]=[]
    messages:list[Message]=Field(min_length=1)
    participants:list[Participant]=[]
    spans:list[Span]=[]
    span_label_status:dict[str,Literal['complete','partial','unannotated']]
    events:list[Event]=[]
    event_arguments:list[Argument]=[]
    relations:list[Relation]=[]
    transactions:dict[str,list[str]]={}
    risk_reference:str|None=None
    risk_basis:list[str]=[]
    missing_information:list[str]=[]
    task_status:dict[str,Literal['complete','partial','unannotated']]

    @model_validator(mode='after')
    def check(self):
        def unique(values):
            if len(values)!=len(set(values)):raise ValueError('duplicate ID')
        for objects in [self.messages,self.spans,self.events,self.participants]:unique([o.id for o in objects])
        ms={m.id:m.text for m in self.messages};ss={s.id:s for s in self.spans};es={e.id:e for e in self.events};ps={p.id:p for p in self.participants}
        if sum(map(len,ms.values()))>10000:raise ValueError('input budget')
        for s in self.spans:
            if s.message_id not in ms or not 0<=s.start<s.end<=len(ms[s.message_id]) or ms[s.message_id][s.start:s.end]!=s.quote:raise ValueError('invalid original evidence')
            if s.label not in SPAN_LABELS:raise ValueError('unknown span label')
        for p in self.participants:
            if p.kind=='mention' and (p.span_id not in ss or ss[p.span_id].label!='entity'):raise ValueError('participant has no entity evidence')
            if p.kind=='metadata' and p.speaker_id not in {m.speaker_id for m in self.messages if m.speaker_id}:raise ValueError('invented metadata speaker')
        for e in self.events:
            if e.anchor_id not in ss or ss[e.anchor_id].label!='action':raise ValueError('event requires action span')
            if set(e.attributes)!=set(ATTRS):raise ValueError('missing attribute keys; use null for unannotated')
            if any(v is not None and v not in ATTRS[k] for k,v in e.attributes.items()):raise ValueError('unknown event attribute')
            if e.transaction_id and (e.transaction_id not in self.transactions or e.id not in self.transactions[e.transaction_id]):raise ValueError('invalid transaction reference')
        for a in self.event_arguments:
            if a.event_id not in es or a.participant_id not in ps or a.role not in ROLES:raise ValueError('invalid role link')
        unique([a.event_id+':'+a.role for a in self.event_arguments])
        for r in self.relations:
            if r.source not in es or r.target not in es or r.source==r.target or r.label not in RELATIONS or not set(r.evidence_refs)<=set(ss):raise ValueError('invalid relation reference')
            if not {es[r.source].anchor_id,es[r.target].anchor_id}<=set(r.evidence_refs):raise ValueError('relation needs both endpoint anchors')
        if any(not set(ids)<=set(es) for ids in self.transactions.values()):raise ValueError('invalid transaction members')
        if self.risk_reference is not None and self.risk_reference not in RISKS:raise ValueError('unknown risk')
        if not set(self.risk_basis)<=set(es):raise ValueError('invalid risk basis')
        if set(self.task_status)!={'spans','attributes','roles','relations','risk'}:raise ValueError('task completeness must be explicit')
        if set(self.span_label_status)!=set(SPAN_LABELS):raise ValueError('span label coverage must be explicit')
        if self.task_status['attributes']=='complete' and any(v is None for e in self.events for v in e.attributes.values()):raise ValueError('complete attributes cannot contain unannotated null')
        if self.task_status['risk']=='complete' and self.risk_reference is None:raise ValueError('complete risk requires a reference label')
        if self.review_status!='draft' and len(set(self.reviewers))<2:raise ValueError('independent review needs two reviewers')
        return self

def runtime_input(sample):
    """Whitelist input fields; NEVER expose labels, groups, transactions or expected rationale."""
    return {'messages':[m.model_dump() for m in sample.messages]}
