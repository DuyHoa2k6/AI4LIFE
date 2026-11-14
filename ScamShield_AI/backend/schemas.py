from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

KEYS = ('claim', 'claimed_identity', 'requested_action', 'persuasion', 'assets_at_risk',
        'impersonation', 'sequence', 'evidence_sufficiency')


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class Message(Strict):
    id: str = Field(min_length=1, max_length=100)
    speaker: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=10000)

    @model_validator(mode='after')
    def nonblank(self):
        if not all(s.strip() for s in (self.id, self.speaker, self.text)):
            raise ValueError('blank message field')
        return self


class OcrReference(Strict):
    message_id: str = Field(min_length=1,max_length=100)
    source_id: str = Field(min_length=1,max_length=100)


class LinkInput(Strict):
    id: str = Field(min_length=1,max_length=100)
    message_id: str = Field(min_length=1,max_length=100)
    url: str = Field(min_length=1,max_length=2048)
    display_text: str = Field(default='',max_length=1000)
    start: int | None = Field(default=None,ge=0)
    end: int | None = Field(default=None,ge=0)
    origin: Literal['dom_href','user_supplied'] = 'user_supplied'


class ClarificationLink(Strict):
    case_id: str = Field(min_length=1,max_length=100)
    situation_id: str = Field(min_length=1,max_length=200)
    revision: int = Field(ge=1)
    content_version: str = Field(pattern=r'^[a-f0-9]{64}$')
    question_id: str = Field(min_length=1,max_length=100)
    answer: str = Field(min_length=1,max_length=1000)


class CaseContext(Strict):
    case_id: str
    situation_id: str
    revision: int
    content_version: str
    question_ids: list[str]
    clarification_status: Literal['initial','accepted','mixed','question','off_topic','unsupported'] = 'initial'


class AnalyzeRequest(Strict):
    clarification: ClarificationLink | None = None
    text: str | None = Field(default=None, min_length=1, max_length=10000)
    messages: list[Message] | None = Field(default=None, min_length=1, max_length=100)
    context: str | None = Field(default=None, max_length=2000)
    question: str | None = Field(default=None, max_length=1000)
    ocr_sources: list[OcrReference] = Field(default_factory=list,max_length=4,exclude_if=lambda v:not v)
    links: list[LinkInput] = Field(default_factory=list,max_length=20,exclude_if=lambda v:not v)

    @model_validator(mode='after')
    def input_valid(self):
        present = self.model_fields_set & {'text', 'messages'}
        if len(present) != 1 or (self.text is None and self.messages is None):
            raise ValueError('provide exactly one non-null text/messages')
        msgs = self.as_messages()
        if sum(len(m.text) for m in msgs) > 10000 or len({m.id for m in msgs}) != len(msgs):
            raise ValueError('content too long or duplicate IDs')
        refs=[r.message_id for r in self.ocr_sources]
        if len(set(refs))!=len(refs) or not set(refs)<={m.id for m in msgs}:
            raise ValueError('invalid OCR message references')
        by_id={m.id:m.text for m in msgs}
        if len({r.id for r in self.links})!=len(self.links):raise ValueError('duplicate link ids')
        for link in self.links:
            if link.message_id not in by_id:raise ValueError('link message not found')
            text=by_id[link.message_id]
            if link.display_text and link.display_text not in text:raise ValueError('link label not in message')
            if link.start is not None or link.end is not None:
                if (link.start is None or link.end is None or link.end<=link.start
                        or text[link.start:link.end]!=link.display_text):raise ValueError('invalid link label offsets')
        return self

    def as_messages(self):
        return self.messages if self.messages is not None else [Message(id='m1', speaker='unknown', text=self.text)]


class Evidence(Strict):
    message_id: str
    quote: str = Field(min_length=1)
    start: int | None = Field(default=None, ge=0)
    end: int | None = Field(default=None, ge=0)


class Answer(Strict):
    status: Literal['observed', 'inferred', 'unknown']
    text: str
    evidence_refs: list[str]


class Answers(Strict):
    claim: Answer
    claimed_identity: Answer
    requested_action: Answer
    persuasion: Answer
    assets_at_risk: Answer
    impersonation: Answer
    sequence: Answer
    evidence_sufficiency: Answer


class Finding(Strict):
    id: str
    action: Literal['transfer_funds', 'share_auth_code', 'grant_access', 'install_app', 'other', 'inducement']
    description: str
    speaker: str
    speech_role: Literal['request', 'quoted_warning', 'denial', 'claim', 'unknown']
    evidence: list[Evidence] = Field(min_length=1, max_length=10)
    inference: Answer


class Extraction(Strict):
    answers: Answers
    findings: list[Finding] = Field(max_length=50)


class RiskLink(Strict):
    request_id: str
    support_id: str


class ContextEvidence(Strict):
    quote: str = Field(min_length=1, max_length=2000)
    start: int = Field(ge=0)
    end: int = Field(ge=0)


class ReviewDecision(Strict):
    risk_links: list[RiskLink] = Field(max_length=50)
    benign_finding_ids: list[str] = Field(max_length=50)
    uncertain_finding_ids: list[str] = Field(max_length=50)
    needs_context: bool
    question_topics: list[Literal['relationship', 'payment_purpose', 'channel', 'file_origin',
                                'permission_purpose', 'source_of_request', 'requested_action',
                                'requested_object', 'action_relation']] = Field(max_length=2)
    context_evidence: list[ContextEvidence] = Field(max_length=5)


class HybridReview(Extraction):
    review: ReviewDecision


class Hypothesis(Strict):
    id: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=500)
    finding_refs: list[str] = Field(min_length=1, max_length=10)
    alternative_explanations: list[str] = Field(max_length=3)


class InitialReview(Extraction):
    hypotheses: list[Hypothesis] = Field(max_length=8)
    uncertainties: list[str] = Field(max_length=4)


class SourceUse(Strict):
    source_id: str
    finding_refs: list[str] = Field(min_length=1, max_length=10)
    relation: Literal['background', 'behavior_support']


class FinalReview(HybridReview):
    source_uses: list[SourceUse] = Field(max_length=3)
    scenario_refs: list[str] = Field(max_length=3)


class FindingUncertainty(Strict):
    finding_id: str
    kind: Literal['identity', 'purpose', 'action', 'relation']


class FinalReviewV2(FinalReview):
    uncertainty_reasons: list[FindingUncertainty] = Field(max_length=50)
    uncertain_relations: list[RiskLink] = Field(default_factory=list, max_length=50)


class RelationAssessment(RiskLink):
    status: Literal['supported', 'uncertain', 'not_supporting_risk']
    relation_type: Literal['payment_required_before_benefit', 'access_required_before_benefit',
                           'installation_required_before_benefit', 'other_prerequisite',
                           'ordinary_transaction', 'unrelated', 'unknown']
    relation_evidence: list[Evidence] = Field(max_length=5)
    assessment_note: str = Field(min_length=1, max_length=400)
    unresolved_reference: str | None = Field(max_length=300)
    missing_information: str | None = Field(max_length=400)


class FinalReviewV3(FinalReviewV2):
    relation_assessments: list[RelationAssessment] = Field(max_length=50)


UrlSignalCode = Literal['userinfo_present','http_transport','ip_literal','nonstandard_port',
    'display_target_mismatch','brand_in_subdomain','lookalike_reference_domain',
    'unicode_confusable_reference','mixed_script_hostname','punycode_hostname',
    'invalid_url','unknown_public_suffix','redirect_domain_change','https_downgrade']


class UrlSignal(Strict):
    code: UrlSignalCode
    level: Literal['info','review']
    detail: str


class RedirectHop(Strict):
    display_url: str
    http_status: int


class UrlNetworkCheck(Strict):
    status: Literal['not_checked','disabled','checked','blocked','timeout','error','redirect_limit','redirect_loop','unsupported','deferred'] = 'not_checked'
    hops: list[RedirectHop] = Field(default_factory=list,max_length=4)
    final_url: str | None = None
    final_hostname: str | None = None
    final_registered_domain: str | None = None
    final_http_status: int | None = None
    reachable: bool | None = None
    elapsed_ms: float = 0
    reason: str | None = None


class UrlAnalysis(Strict):
    link_id: str
    message_id: str
    origin: Literal['dom_href','user_supplied','text','ocr']
    status: Literal['parsed','invalid']
    display_url: str
    hostname: str | None = None
    unicode_hostname: str | None = None
    registered_domain: str | None = None
    reference_domain: str | None = None
    label_status: Literal['grounded','ambiguous','none']
    signals: list[UrlSignal]
    reputation_status: Literal['not_checked'] = 'not_checked'
    network: UrlNetworkCheck = Field(default_factory=UrlNetworkCheck)


class UrlUse(Strict):
    link_id: str
    signal_codes: list[UrlSignalCode] = Field(max_length=12)
    finding_refs: list[str] = Field(max_length=10)
    relation: Literal['supports_request_risk','background','quoted_warning']


class FinalReviewV4(FinalReviewV3):
    url_uses: list[UrlUse] = Field(max_length=20)


class RuleHintReview(Strict):
    hint_id: str
    interpretation: Literal['request','claim','denial','quoted_warning','not_supported','uncertain']
    evidence: list[Evidence] = Field(min_length=1,max_length=3)
    finding_refs: list[str] = Field(max_length=10)
    missing_information: str | None


class FinalReviewV5(FinalReviewV4):
    rule_hint_reviews: list[RuleHintReview] = Field(max_length=12)


# Provider output references immutable input IDs; authors are joined by the backend.
class FindingDraft(Strict):
    id: str
    action: Literal['transfer_funds','share_auth_code','grant_access','install_app','other','inducement']
    description: str
    speech_role: Literal['request','quoted_warning','denial','claim','unknown']
    evidence: list[Evidence] = Field(min_length=1,max_length=10)
    inference: Answer


class InitialReviewDraft(InitialReview):
    findings: list[FindingDraft] = Field(max_length=50)


SituationKind = Literal['asset_handover_requested','payment_not_confirmed','payment_received_reported',
    'changed_payee_transfer_requested','verification_after_payment_requested','identity_documents_requested',
    'screen_sharing_requested','banking_view_requested','code_requested','login_code_identified',
    'payment_requested','ordinary_transaction_reported','unspecified_confirmation_step','withdrawal_pending_without_next_step']


class SituationFact(Strict):
    id: str
    kind: SituationKind
    speech_role: Literal['request','claim','quoted_warning','denial','unknown']
    evidence: list[Evidence] = Field(min_length=1,max_length=3)
    context_evidence: list[ContextEvidence] = Field(max_length=2)
    finding_refs: list[str] = Field(max_length=5)


SituationLinkKind = Literal['handover_before_payment_confirmation','handover_after_reported_payment',
    'changed_payee_before_verification','screen_share_banking','code_request_is_login_code','ordinary_payment_context']


class SituationLink(Strict):
    kind: SituationLinkKind
    fact_ids: list[str] = Field(min_length=2,max_length=3)
    status: Literal['supported','uncertain','not_applicable']
    evidence: list[Evidence] = Field(min_length=1,max_length=4)
    missing_information: str | None


GapKind = Literal['requested_step','requested_object','withdrawal_next_requirement','payment_purpose',
    'payment_confirmation','action_relation','requester_identity','file_origin','permission_purpose','channel']


class InformationGap(Strict):
    kind: GapKind
    evidence: list[Evidence] = Field(min_length=1,max_length=3)
    finding_refs: list[str] = Field(max_length=5)
    affects_decision: bool


class FinalReviewV6(FinalReviewV5):
    situation_facts: list[SituationFact] = Field(max_length=16)
    situation_links: list[SituationLink] = Field(max_length=10)
    information_gaps: list[InformationGap] = Field(max_length=5)


class FinalReviewDraftV6(FinalReviewV6):
    findings: list[FindingDraft] = Field(max_length=50)


class RetrievalBranch(Strict):
    status: Literal['disabled', 'no_approved_sources', 'no_match', 'matched', 'timeout', 'error']
    retrieved_count: int = Field(ge=0)
    elapsed_ms: float = Field(ge=0)


class RetrievalTrace(Strict):
    scenarios: RetrievalBranch
    official_sources: RetrievalBranch


class AnalysisTrace(Strict):
    pipeline: Literal['local_rules'] = 'local_rules'
    routing: Literal['local_backend'] = 'local_backend'
    rules_version: str
    preliminary_status: Literal['completed', 'limited']
    preliminary_risk: str | None
    preliminary_findings: int
    rule_conflicts: int
    rule_hints_reviewed: int = 0
    rule_hints_reclassified: int = 0
    rule_hints_uncertain: int = 0
    observation_repairs: int = 0
    situation_facts: int = 0
    situation_links: int = 0
    information_gaps: int = 0
    discarded_live_findings: int
    live_status: Literal['not_used'] = 'not_used'
    initial_findings: int = 0
    initial_hypotheses: int = 0
    discarded_source_uses: int = 0
    scenario_matches: list[str] = []
    stage_timings_ms: dict[str, float] = {}
    decision_version: str | None = None
    information_needed: bool = False
    consistency_repairs: int = 0
    consistency_issues: list[str] = Field(default_factory=list)
    grounded_relation_count: int = 0
    relation_review_candidates: int = 0
    unresolved_relation_candidates: int = 0
    discarded_url_uses: int = 0
    used_url_evidence: int = 0


class SourceMatch(Strict):
    source_id: str
    url: str
    quote: str
    match_level: Literal['background', 'behavior_support', 'exact_entity']
    reviewed_at: str
    valid_until: str | None


class OcrBox(Strict):
    x0: int
    y0: int
    x1: int
    y1: int


class OcrBlock(Strict):
    text: str
    confidence: float
    bbox: OcrBox


class OcrResponse(Strict):
    source_id: str | None
    image_sha256: str
    text: str = Field(max_length=10000)
    status: Literal['ready','low_confidence','no_text']
    confidence: float
    engine: str
    width: int
    height: int
    blocks: list[OcrBlock] = Field(max_length=500)
    ocr_ms: float
    notice: str


class OcrInputSource(Strict):
    message_id: str
    image_id: str
    origin: Literal['image_ocr']
    image_sha256: str
    confidence: float
    width: int
    height: int
    blocks: list[OcrBlock]
    verification: Literal['matches_ocr_output_not_verified_pixels']


class RiskIndicator(Strict):
    kind: str
    evidence: list[Evidence]
    explanation: str


class AnalyzeResponse(Strict):
    request_id: str | None = Field(default=None,exclude_if=lambda v:v is None)
    case_context: CaseContext | None = None
    schema_version: str = '1.0'
    mode: Literal['mock','local_rules']
    risk_status: Literal['clear', 'need_context', 'suspicious', 'high']
    summary: str
    answers: Answers
    findings: list[Finding]
    suspected_scam_types: list[str] = []
    missing_information: list[str]
    follow_up_questions: list[str] = Field(max_length=2)
    recommended_actions: list[str]
    answer_to_user: str | None
    source_matches: list[SourceMatch] = []
    analysis: AnalysisTrace | None = None
    retrieval: RetrievalTrace | None = None
    input_sources: list[OcrInputSource] = Field(default_factory=list)
    input_warnings: list[str] = Field(default_factory=list)
    url_analysis: list[UrlAnalysis] = Field(default_factory=list)
    url_uses: list[UrlUse] = Field(default_factory=list)
    display_summary: str | None = Field(default=None,max_length=600,exclude_if=lambda v:v is None)
    display_action: str | None = Field(default=None,max_length=600,exclude_if=lambda v:v is None)
    risk_indicators: list[RiskIndicator] = Field(default_factory=list,exclude_if=lambda v:not v)
    safety_urgency: Literal['undetermined','preventive','urgent'] = 'undetermined'
    urgency_evidence: list[Evidence] = Field(default_factory=list,exclude_if=lambda v:not v)
    analysis_status: Literal['complete','partial','unsupported','error'] = 'complete'


class ErrorResponse(Strict):
    code: str
    message: str
    request_id: str
    diagnostic: dict | None = None
