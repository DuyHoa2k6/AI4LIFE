from datetime import datetime
from typing import Literal
from pydantic import Field, model_validator
from ..schemas import Strict, AnalyzeRequest, Message, UrlAnalysis, UrlUse, RiskIndicator, RetrievalBranch
from ..local_observation.schema import Answers18
from .fact_schema import FactTrace
from .interpretation_schema import Interpretation

Review = Literal['weak_label','draft','pending_review','reviewed']
Risk = Literal['clear','need_context','suspicious','high']
Urgency = Literal['undetermined','preventive','urgent']
EventType = Literal['transfer_funds','receive_funds','withdraw_funds','handover_asset','provide_code',
 'provide_credentials','provide_documents','open_link','login','install_app','share_screen','grant_control',
 'change_channel','keep_secret','avoid_verification','identity_claim','relationship_claim','code_identity',
 'build_trust','invite_travel_or_meeting','offer_employment','change_destination_or_terms','impose_debt',
 'request_secrecy','restrict_communication','retain_identity_documents','restrict_movement','threaten_harm',
 'threaten_disclosure','demand_release_payment','compel_work','compel_illegal_activity','bodily_integrity_threat',
 'return_documents_available','free_to_leave','consent_and_exit_available','other',
 'sign_obligation','guarantee_debt','misstate_information','purchase_asset','transfer_ownership',
 'grant_authority','confirm_completion','release_funds','withhold_wages','recover_access',
 'grant_asset_access','return_funds','verification_status','verification_request','describe_terms']
RelationType = Literal['prerequisite_for','before','after','reason_given_for','contradiction','state_update',
 'reported_by','warning_about','same_transaction','travel_conditioned_on_secrecy','movement_restricted_by_debt',
 'document_retention_limits_exit','threat_used_to_compel_action','release_conditioned_on_payment','work_differs_from_agreement',
 'same_object','obstructs_verification','transfer_via','promised_after','threatens_unless','controls_during','supersedes',
 'funding_ownership_mismatch','exceeds_scope','transfers_control','unverified_authority','liability_if_default','coerced_by']


class InputMessage(Strict):
    id: str = Field(min_length=1,max_length=100)
    speaker_id: str | None = Field(default=None,max_length=100)
    text: str = Field(min_length=1,max_length=10000)
    timestamp: datetime | None = None
    content_type: Literal['text','post','comment','email','ocr'] = 'text'
    parent_message_id: str | None = None
    scope_id: str | None = Field(default=None,max_length=100)


class ContextFact(Strict):
    id: str = Field(min_length=1,max_length=100)
    text: str = Field(min_length=1,max_length=2000)
    source: Literal['user_report'] = 'user_report'
    verification_status: Literal['unverified','user_reports_verification'] = 'unverified'
    applies_to_message_ids: list[str] = Field(default_factory=list,max_length=100)
    scope_id: str | None = None


class CaseInput(Strict):
    messages: list[InputMessage] = Field(min_length=1,max_length=100)
    context_facts: list[ContextFact] = Field(default_factory=list,max_length=10)
    user_question: str | None = Field(default=None,max_length=1000)

    @model_validator(mode='after')
    def valid_input(self):
        ids=[m.id for m in self.messages]
        if len(ids)!=len(set(ids)) or sum(len(m.text) for m in self.messages)>10000:raise ValueError('invalid input budget or IDs')
        if len({c.id for c in self.context_facts})!=len(self.context_facts) or sum(len(c.text) for c in self.context_facts)>2000:raise ValueError('invalid context budget or IDs')
        for m in self.messages:
            if not m.text.strip() or not m.id.strip() or (m.speaker_id is not None and not m.speaker_id.strip()):raise ValueError('blank input')
            if m.parent_message_id and (m.parent_message_id not in ids or ids.index(m.parent_message_id)>=ids.index(m.id)):raise ValueError('invalid parent order')
        if any(not set(c.applies_to_message_ids)<=set(ids) for c in self.context_facts):raise ValueError('invalid context targets')
        return self

    def legacy(self):
        return AnalyzeRequest(messages=[Message(id=m.id,speaker=m.speaker_id or 'unknown',text=m.text) for m in self.messages],
            context='\n'.join(c.text for c in self.context_facts) or None,question=self.user_question)


class Metadata(Strict):
    case_id: str
    schema_version: Literal['scamshield-case-2.0'] = 'scamshield-case-2.0'
    language: str = 'vi'
    channel: Literal['chat','comment','post','email','ocr','mixed','unknown'] = 'unknown'
    family_id: str
    scenario_id: str
    variant_group_id: str
    source_id: str | None = None
    source_group_id: str | None = None
    origin_type: Literal['synthetic','consented_real','source_based_simulation']
    review_status: Review
    annotation_version: str
    split: Literal['pilot','train','dev','test','independent']
    license_or_permission: str | None = None
    reviewers: list[str] = Field(default_factory=list)


class Span(Strict):
    span_id: str
    message_id: str | None
    context_id: str | None = None
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    quote: str = Field(min_length=1)
    label: Literal['verb','action','object','negation','state','time','condition','purpose','participant',
        'organization','url','account','application','quotation','reported_speech','persuasion','statement']
    review_status: Review = 'weak_label'


class Participant(Strict):
    participant_id: str
    label: str
    interaction_role: Literal['speaker','buyer','seller','requester','recipient','affected_party','mentioned','unknown']
    identity_status: Literal['claimed','user_reported','unknown'] = 'unknown'
    evidence_refs: list[str] = Field(default_factory=list)
    claimed_identity: str | None = None
    relationship_to_user: str | None = None
    information_status: Literal['observed','claimed','user_reported','inferred','unknown'] = 'unknown'


class PersonalRelationship(Strict):
    participant_ids: list[str] = Field(min_length=2,max_length=2)
    relationship_type: Literal['family','friend','colleague','online_only','unknown']
    status: Literal['observed','claimed','user_reported','unknown']
    evidence_refs: list[str]
    scope_id: str | None = None
    valid_at: datetime | None = None


class Attribution(Strict):
    speaker_id: str | None
    kind: Literal['sender_claim','self_report','reported','quoted_warning','hypothetical','user_report','unknown']
    verification_status: Literal['unverified','user_reports_verification'] = 'unverified'


class SemanticEvent(Strict):
    clause_id: str | None = None
    arguments: dict[str,str | None] = Field(default_factory=dict)
    right_scope: str | None = None
    epistemic_state: Literal['known','unverified','unknown','alternatives'] = 'known'
    alternatives: list[str] = Field(default_factory=list)
    traits: list[str] = Field(default_factory=list)
    message_id: str | None
    context_id: str | None = None
    situation_id: str
    speaker_id: str | None = None
    requester_id: str | None = None
    performer_id: str | None = None
    affected_party_id: str | None = None
    normalized_action: str
    object_type: str | None = None
    transfer_source: str | None = None
    transfer_destination: str | None = None
    negation_scope_refs: list[str] = []
    stated_condition: str | None = None
    stated_time: str | None = None
    information_status: Literal['observed','claimed','user_reported','inferred','unknown'] = 'unknown'
    is_reported_request: bool = False
    extraction_method: str = 'local_structural_patterns_v1'
    speech_act: str | None = None
    condition: dict | None = None
    consequence_refs: list[str] = []
    mention_refs: list[str] = []
    transaction_reference: str | None = None
    transaction_binding: Literal['explicit_code','direct_reference','unresolved'] = 'unresolved'


class Event(Strict):
    event_id: str
    event_type: EventType
    description: str
    actor_id: str | None
    recipient_id: str | None = None
    affected_party_id: str | None = None
    object: str | None = None
    polarity: Literal['positive','negative','uncertain']
    modality: Literal['request','assertion','report','conditional','threat','possibility','unknown']
    temporal_state: Literal['requested','completed','pending','ongoing','imminent','planned','hypothetical','past','unknown']
    speech_role: Literal['request','claim','reported','quoted_warning','denial','hypothetical','unknown']
    attribution: Attribution
    status: Literal['observed','claimed','inferred','unknown']
    scope_id: str | None
    event_time: str | None = None
    evidence_refs: list[str] = Field(min_length=1)
    extractor_rule_id: str
    unknown_fields: list[str] = Field(default_factory=list)
    stated_purpose: str | None = None
    semantic: SemanticEvent | None = None


class Relation(Strict):
    relation_id: str
    type: RelationType
    from_id: str
    to_id: str
    evidence_refs: list[str] = Field(min_length=1)
    status: Literal['observed','claimed','inferred','unknown']
    scope_id: str | None
    rationale: str
    rule_id: str


class Annotations(Strict):
    participants: list[Participant]
    spans: list[Span]
    events: list[Event]
    personal_relationships: list[PersonalRelationship] = Field(default_factory=list)
    relations: list[Relation]
    answers_18: Answers18
    limitations: list[str] = Field(default_factory=list)
    graph_trace: dict = Field(default_factory=dict)
    mentions: list['PersonMention'] = []
    grounding_trace: dict = Field(default_factory=dict)


class PersonMention(Strict):
    mention_id: str
    message_id: str
    scope_id: str
    role: str
    participant_id: str | None = None
    candidate_ids: list[str] = []
    resolution: Literal['explicit_name','unique_antecedent','unresolved']
    evidence_refs: list[str]


class Assessment(Strict):
    risk_status: Risk | None
    safety_urgency: Urgency
    supported_conclusions: list[str]
    evidence_refs: list[str]
    urgency_evidence_refs: list[str] = Field(default_factory=list)
    applicable_rule_ids: list[str]
    missing_information: list[str]
    follow_up_questions: list[str] = Field(max_length=2)
    recommended_actions: list[str]
    explanation_template_id: str
    prohibited_conclusions: list[str]
    summary: str


class DatasetCase(Strict):
    metadata: Metadata
    input: CaseInput
    annotations: Annotations
    expected_assessment: Assessment | None


class SourceSupport(Strict):
    source_id: str
    url: str
    quote: str
    relation: Literal['background_only','behavior_support'] = 'background_only'
    event_refs: list[str] = Field(default_factory=list)
    reviewed_at: str
    valid_until: str | None
    entity_verified: Literal[False] = False


class SupportContact(Strict):
    id: str
    region: str
    label: str
    channel: Literal['phone','url']
    value: str
    source_url: str
    reviewer: str
    checked_at: str
    valid_until: str


class LocalResult(Strict):
    schema_version: Literal['local-reasoning-2.0'] = 'local-reasoning-2.0'
    mode: Literal['local_rules'] = 'local_rules'
    analysis_status: Literal['complete','partial','unsupported','error']
    input_sha256: str
    annotations: Annotations
    assessment: Assessment
    knowledge_status: str
    source_matches: list[SourceSupport] = Field(default_factory=list,max_length=3)
    support_contacts: list[SupportContact] = Field(default_factory=list)
    versions: dict[str,str]
    elapsed_ms: float
    url_analysis: list[UrlAnalysis] = Field(default_factory=list)
    url_uses: list[UrlUse] = Field(default_factory=list)
    support_indicators: list[RiskIndicator] = Field(default_factory=list)
    official_retrieval: RetrievalBranch | None = None
    support_timings_ms: dict[str,float] = Field(default_factory=dict)
    support_warnings: list[str] = Field(default_factory=list)
    fact_trace: FactTrace | None = None
    core_timings_ms: dict[str,float] = Field(default_factory=dict)
    interaction_frames: list['InteractionFrame'] = Field(default_factory=list)
    interpretation: Interpretation | None = None


class InteractionFrame(Strict):
    frame_id: str
    requester_id: str | None
    target_id: str | None
    scope_id: str
    speech_role: Literal['request','claim','reported','quoted_warning','denial','hypothetical','unknown']
    action_event_id: str
    requested_action: str
    stated_purpose: str | None = None
    condition: str | None = None
    benefit_event_id: str | None = None
    possible_effect: str
    evidence_refs: list[str]
    missing_information: list[str] = Field(default_factory=list)
    communication_functions: list[str] = Field(default_factory=list)


LocalResult.model_rebuild()
