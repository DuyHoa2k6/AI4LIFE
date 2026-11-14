"""Versioned first-stage contract, independent of final risk classification."""
from typing import Literal
from pydantic import Field
from ..schemas import Strict, InitialReview

Status = Literal['observed', 'claimed', 'user_reported', 'inferred', 'unknown']


class Span(Strict):
    id: str
    source: Literal['message', 'context'] = 'message'
    provenance: Literal['text', 'user_report'] = 'text'
    message_id: str | None
    speaker: str | None
    kind: Literal['verb', 'action', 'target', 'negation', 'time', 'statement']
    start: int
    end: int
    quote: str


class Unit(Strict):
    message_id: str
    speaker: str
    sentence_id: str
    start: int
    end: int
    quote: str
    quoted: bool
    boundary_reason: str = 'sentence_start'
    boundary_status: Literal['observed','inferred','uncertain'] = 'observed'
    limitations: list[str] = Field(default_factory=list)


class Participant(Strict):
    id: str
    label: str
    role: Literal['speaker', 'addressee', 'mentioned']
    provenance: Literal['metadata', 'text', 'user_report']
    identity_verified: bool = False
    evidence_refs: list[str] = Field(default_factory=list)


class Event(Strict):
    action_id: str
    action_type: Literal['transfer_funds', 'receive_funds', 'withdraw_funds', 'handover_asset',
        'provide_code', 'provide_credentials', 'provide_documents', 'open_link', 'login',
        'install_app', 'share_screen', 'grant_control', 'change_channel', 'keep_secret',
        'avoid_verification', 'identity_claim', 'relationship_claim', 'code_identity']
    verb_span: str
    action_span: str
    target_span: str | None = None
    negation_span: str | None = None
    time_span: str | None = None
    actor: str | None
    recipient: str | None = None
    beneficiary: str | None = None
    target: str | None = None
    location: str | None = None
    polarity: Literal['positive', 'negative', 'uncertain']
    speech_role: Literal['request', 'claim', 'reported', 'quoted_warning', 'unknown']
    temporal_state: Literal['requested', 'completed', 'pending', 'hypothetical', 'unknown']
    time_expression: str | None = None
    transaction_id: str | None = None
    evidence_refs: list[str]
    rule_id: str
    limitations: list[str] = Field(default_factory=list)


class Relation(Strict):
    relation_id: str
    type: Literal['prerequisite_for', 'before', 'after', 'reason_given_for', 'contradiction',
                  'state_update', 'warning_about', 'reported_by']
    from_id: str
    to_id: str
    evidence_refs: list[str]
    rule_id: str
    status: Status
    limitations: list[str] = Field(default_factory=list)


class Value(Strict):
    statements: list[str] = Field(default_factory=list)
    event_ids: list[str] = Field(default_factory=list)
    participant_ids: list[str] = Field(default_factory=list)
    relation_ids: list[str] = Field(default_factory=list)


class AnalysisField(Strict):
    status: Status = 'unknown'
    value: Value = Field(default_factory=Value)
    evidence_refs: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    extraction_method: str | None = None
    rule_ids: list[str] = Field(default_factory=list)


class Answers18(Strict):
    situation: AnalysisField
    participants: AnalysisField
    sender_identity: AnalysisField
    relationship: AnalysisField
    communication_channel: AnalysisField
    claims: AnalysisField
    requested_actions: AnalysisField
    action_targets: AnalysisField
    stated_purpose: AnalysisField
    assets_and_access: AnalysisField
    benefit_and_mismatch: AnalysisField
    persuasion: AnalysisField
    conditions_and_sequence: AnalysisField
    contradictions_and_alternatives: AnalysisField
    technical_checks: AnalysisField
    evidence_quality: AnalysisField
    missing_information: AnalysisField
    assessment: AnalysisField


class AbbreviationResolution(Strict):
    message_id: str | None
    source: Literal['message','context'] = 'message'
    start: int
    end: int
    quote: str
    status: Literal['resolved','ambiguous','unresolved']
    expansion: str | None
    alternatives: list[str]
    rule_ids: list[str]
    basis: str


class Observation(Strict):
    schema_version: Literal['observation-1.0'] = 'observation-1.0'
    mode: Literal['python_rules'] = 'python_rules'
    rules_version: str
    rules_sha256: str
    input_sha256: str
    abbreviation_version: str = ''
    abbreviation_sha256: str = ''
    abbreviation_resolutions: list[AbbreviationResolution] = Field(default_factory=list)
    units: list[Unit]
    participants: list[Participant]
    evidence: list[Span]
    events: list[Event]
    relations: list[Relation]
    answers_18: Answers18
    follow_up_questions: list[str] = Field(max_length=2)
    limitations: list[str]
    adapter: InitialReview
    elapsed_ms: float
