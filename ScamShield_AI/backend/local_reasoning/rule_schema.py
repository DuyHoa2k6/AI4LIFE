from typing import Literal
from pydantic import Field
from ..schemas import Strict
from .schema import EventType,RelationType,Risk,Urgency


class Fact(Strict):
    event_types: list[EventType] = Field(min_length=1)
    polarities: list[Literal['positive','negative','uncertain']] = ['positive']
    speech_roles: list[str] = ['request','claim','reported']
    temporal_states: list[str] = []
    attribution_kinds: list[str] = []
    requires_authentication_meaning: bool = False
    extractor_rule_ids: list[str] = []


class RelationCondition(Strict):
    type: RelationType
    from_fact: str
    to_fact: str


class Rule(Strict):
    rule_id: str
    version: str
    description: str
    scope: Literal['same_event','same_scope_same_affected_party']
    required_facts: dict[str,Fact]
    required_relations: list[RelationCondition]
    exclusions: list[Literal['later_payment_confirmed','documents_returnable','consent_without_coercion']] = []
    missing_fact_policy: Literal['ask','ignore']
    conclusion: Risk
    safety_urgency: Urgency = 'preventive'
    evidence_requirements: Literal['all_required_facts_and_relations']
    follow_up_question_template: str | None
    explanation_template_id: str
    supported_conclusion: str
    test_case_ids: list[str]


class Rulebook(Strict):
    version: str
    rules: list[Rule] = Field(max_length=40)


class ExplanationTemplate(Strict):
    summary: str = Field(min_length=1,max_length=1000)
    recommended_actions: list[str] = Field(max_length=5)
    required_slots: list[Literal['verified_quotes']]
    fallback_template_id: str | None


class Templates(Strict):
    version: str
    templates: dict[str,ExplanationTemplate]


class ExtractionRule(Strict):
    id: str
    event_type: EventType
    pattern: str = Field(min_length=1,max_length=1000)


class ExtractionRules(Strict):
    version: str
    review_status: Literal['controlled_project_rules']
    rules: list[ExtractionRule] = Field(max_length=40)


class EventLabel(Strict):
    id: EventType
    definition: str
    counterexample: str


class RelationLabel(Strict):
    id: RelationType
    definition: str


class LabelCatalog(Strict):
    version: str
    events: list[EventLabel]
    relations: list[RelationLabel]
    span_labels: list[str]
    risk_status: list[Risk]
    safety_urgency: list[Urgency]
    disallowed_shortcuts: list[str]
    participant_roles: list[str] = []
    personal_relationship_types: list[str] = []
