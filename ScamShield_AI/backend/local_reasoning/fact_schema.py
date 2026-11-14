"""Typed three-valued fact contract; absence is never a negative observation."""
from datetime import datetime
from enum import Enum
from typing import Literal
from pydantic import Field, model_validator
from ..schemas import Strict


class Truth(str,Enum):
    TRUE='TRUE'
    FALSE='FALSE'
    UNKNOWN='UNKNOWN'


def conjunction(values):
    values=list(values)
    if any(v is Truth.FALSE for v in values):return Truth.FALSE
    if any(v is Truth.UNKNOWN for v in values):return Truth.UNKNOWN
    return Truth.TRUE


class FactRecord(Strict):
    fact_id: str
    fact_type: str
    value: Truth
    participant_ids: list[str] = Field(default_factory=list)
    scope_id: str | None
    transaction_id: str | None = None
    source: Literal['observed_content','sender_claim','user_report','technical_check','derived']
    evidence_refs: list[str] = Field(default_factory=list)
    event_time: str | None = None
    observed_at: datetime
    version: int = 1
    dependency_refs: list[str] = Field(default_factory=list)
    rule_id: str | None = None
    event_id: str | None = None
    attributes: dict[str,str] = Field(default_factory=dict)
    superseded_by: str | None = None

    @model_validator(mode='after')
    def grounded(self):
        if self.value is not Truth.UNKNOWN and not self.evidence_refs:raise ValueError('Known fact needs evidence')
        if self.source=='derived' and (not self.dependency_refs or not self.rule_id):raise ValueError('Derived fact needs dependencies and rule')
        return self


class Condition(Strict):
    fact_types: list[str] = Field(min_length=1)
    value: Truth = Truth.TRUE
    speech_roles: list[str] = ['request','claim','reported']
    temporal_states: list[str] = []
    attribution_kinds: list[str] = []
    authentication_meaning: Truth | None = None


class RelationRequirement(Strict):
    type: str
    from_fact: str
    to_fact: str


class FactRule(Strict):
    rule_id: str
    version: str
    scope: Literal['same_event','same_scope_same_affected_party']
    required_conditions: dict[str,Condition]
    required_relations: list[RelationRequirement] = []
    exclusion_conditions: list[Literal['later_payment_confirmed','documents_returnable','consent_without_coercion']] = []
    conclusion: Literal['high','suspicious','need_context','clear']
    safety_urgency: Literal['urgent','preventive','undetermined'] = 'preventive'
    evidence_requirements: Literal['all_required_facts_and_relations']
    missing_information: list[str] = []
    follow_up_template: str | None = None
    explanation_template: str
    supported_conclusion: str
    unknown_exclusion_policy: Literal['limit_claim','undetermined'] = 'limit_claim'


class FactRulebook(Strict):
    version: str
    rules: list[FactRule] = Field(min_length=1,max_length=50)

    @model_validator(mode='after')
    def valid_rules(self):
        if len({r.rule_id for r in self.rules})!=len(self.rules):raise ValueError('Duplicate fact rule')
        for r in self.rules:
            if not r.required_conditions:raise ValueError('Empty rule')
            for relation in r.required_relations:
                if not {relation.from_fact,relation.to_fact}<=r.required_conditions.keys():raise ValueError('Unknown rule slot')
        return self


class RuleEvaluation(Strict):
    rule_id: str
    version: str
    status: Literal['MATCHED','NOT_MATCHED','UNDETERMINED']
    fact_refs: list[str] = []
    evidence_refs: list[str] = []
    missing_information: list[str] = []
    exclusion_state: Truth = Truth.UNKNOWN
    scope_id: str | None = None


class FactTrace(Strict):
    version: str = 'three-valued-facts-1.0'
    facts: list[FactRecord]
    rule_evaluations: list[RuleEvaluation]
    conflicts: list[list[str]] = []
    discarded_event_ids: list[str] = []
    stage_timings_ms: dict[str,float] = {}
    external_evidence: dict[str,dict] = {}
