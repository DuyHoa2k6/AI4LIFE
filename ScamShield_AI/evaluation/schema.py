from typing import Literal
from pydantic import Field,model_validator
from ml.phobert.schema import Strict,Message,Span,Participant,Argument,Event,RELATIONS,ROLES,RISKS
from .ontology import POLICY_ATTRS

class Input(Strict):
    messages:list[Message]=Field(min_length=1,max_length=100)
    context:str|None=None

class ExpectedEvent(Event):
    description:str
    information_status:Literal['observed','claimed','user_reported','inferred','unknown']
    argument_refs:list[str]=[]

class ExpectedRelation(Strict):
    id:str
    type:str
    source_id:str
    target_id:str
    scope_id:str|None
    evidence_refs:list[str]=Field(min_length=1)

class Situation(Strict):
    id:str
    event_refs:list[str]
    participant_refs:list[str]

class Expected(Strict):
    participants:list[Participant]
    spans:list[Span]
    events:list[ExpectedEvent]
    event_arguments:list[Argument]
    relations:list[ExpectedRelation]
    cases:list[Situation]
    risk_status:Literal['clear','need_context','suspicious','high']
    rationale:str
    decisive_event_refs:list[str]
    mechanism_tags:list[str]
    missing_information:list[str]
    acceptable_question_targets:list[str]
    acceptable_questions:list[str]
    contradictions:list[str]
    forbidden_inferences:list[str]

class Case(Strict):
    schema_version:Literal['evaluation-case-1.0']='evaluation-case-1.0'
    case_id:str
    family_id:str
    template_id:str
    source_group:str
    split:Literal['diagnostic','validation','regression','locked']
    domain:Literal['education','relationships','finance','employment','services','data_access','contributions']
    provenance:dict[str,str]
    novelty:Literal['seen_development','new_public_draft']
    review_status:Literal['draft','human_verified','adjudicated']
    reviewer_reference:list[str]=[]
    annotation_ambiguity:list[str]=[]
    input:Input
    expected:Expected
    annotation_completeness:dict[str,Literal['complete','partial','unannotated']]
    phenomena:list[str]
    metamorphic_parent:str|None=None
    metamorphic_relation:str|None=None

    @model_validator(mode='after')
    def check(self):
        ms={m.id:m for m in self.input.messages};e=self.expected
        if len(ms)!=len(self.input.messages) or sum(len(m.text) for m in ms.values())>10000:raise ValueError('invalid message IDs/budget')
        for items in [e.spans,e.events,e.participants,e.relations,e.cases]:
            if len({x.id for x in items})!=len(items):raise ValueError('duplicate expected ID')
        ss={s.id:s for s in e.spans};es={v.id:v for v in e.events};ps={p.id:p for p in e.participants};scopes={s.id:s for s in e.cases}
        for s in e.spans:
            if s.message_id not in ms or not 0<=s.start<s.end<=len(ms[s.message_id].text) or ms[s.message_id].text[s.start:s.end]!=s.quote:raise ValueError('invalid evidence offset')
        for p in e.participants:
            if p.kind=='metadata' and p.speaker_id not in {m.speaker_id for m in ms.values() if m.speaker_id}:raise ValueError('invented speaker metadata')
            if p.kind=='mention' and (p.span_id not in ss or ss[p.span_id].label!='entity'):raise ValueError('missing mention evidence')
            if p.kind=='unknown' and not p.id.startswith('unknown:'):raise ValueError('unknown participants require separate scoped placeholders')
        for v in e.events:
            if v.anchor_id not in ss or ss[v.anchor_id].label!='action':raise ValueError('event lacks action evidence')
            if set(v.attributes)!=set(POLICY_ATTRS) or any(x is not None and x not in POLICY_ATTRS[k] for k,x in v.attributes.items()):raise ValueError('attribute outside versioned policy ontology')
            if v.transaction_id and (v.transaction_id not in scopes or v.id not in scopes[v.transaction_id].event_refs):raise ValueError('wrong event scope')
            if not set(v.argument_refs)<=set(ss):raise ValueError('invalid argument span')
        for a in e.event_arguments:
            if a.event_id not in es or a.role not in ROLES or a.participant_id not in ps:raise ValueError('dangling participant/role')
        if len({(a.event_id,a.role) for a in e.event_arguments})!=len(e.event_arguments):raise ValueError('duplicate event role')
        for r in e.relations:
            if r.type not in RELATIONS or r.source_id not in es or r.target_id not in es or r.source_id==r.target_id:raise ValueError('invalid event relation')
            if not {es[r.source_id].anchor_id,es[r.target_id].anchor_id}<=set(r.evidence_refs) or not set(r.evidence_refs)<=set(ss):raise ValueError('relation lacks endpoint evidence')
            a,b=es[r.source_id],es[r.target_id]
            if a.transaction_id and b.transaction_id and a.transaction_id!=b.transaction_id:raise ValueError('cross-transaction expected relation')
            if r.scope_id and r.scope_id not in scopes:raise ValueError('dangling relation scope')
            if r.type=='state_update' and (a.attributes['action_type']!=b.attributes['action_type'] or a.attributes['object_type']!=b.attributes['object_type']):raise ValueError('state update changes object/action')
        for s in e.cases:
            if not set(s.event_refs)<=set(es) or not set(s.participant_refs)<=set(ps):raise ValueError('dangling case scope')
        if not set(e.decisive_event_refs)<=set(es):raise ValueError('invalid decisive event')
        if set(self.annotation_completeness)!={'spans','events','roles','relations','risk','explanation','questions'}:raise ValueError('task completeness must be explicit')
        if self.review_status!='draft' and len(set(self.reviewer_reference))<2:raise ValueError('review status needs actual independent reviewer references')
        if not self.provenance.get('origin') or not self.provenance.get('source_ref'):raise ValueError('missing provenance')
        return self

def runtime_input(case):
    return {'messages':[m.model_dump() for m in case.input.messages]}

def oracle_graph(case):
    e=case.expected;by_id={s.id:s for s in e.spans};messages={m.id:m for m in case.input.messages}
    return {'spans':[s.model_dump() for s in e.spans],
      'events':[{'id':v.id,'anchor_id':v.anchor_id,'attributes':v.attributes,'speaker_id':messages[by_id[v.anchor_id].message_id].speaker_id,
         'roles':{a.role:next(('speaker:'+p.speaker_id if p.kind=='metadata' else p.id for p in e.participants if p.id==a.participant_id),None) for a in e.event_arguments if a.event_id==v.id},
         'transaction_id':v.transaction_id,'information_status':v.information_status,'argument_refs':v.argument_refs} for v in e.events],
      'relations':[{'id':r.id,'label':r.type,'source':r.source_id,'target':r.target_id,'scope_id':r.scope_id,'evidence_refs':r.evidence_refs} for r in e.relations],
      'limitations':[]}
