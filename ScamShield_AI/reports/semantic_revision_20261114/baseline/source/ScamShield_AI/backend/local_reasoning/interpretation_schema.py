from typing import Literal
from pydantic import Field
from ..schemas import Strict

Information=Literal['observed','claimed','user_reported','inferred','unknown']


class Behavior(Strict):
    behavior_id: str
    behavior_type: str
    actor_id: str | None
    affected_party_id: str | None
    event_refs: list[str]
    description: str
    information_status: Information
    evidence_refs: list[str]
    rule_id: str
    scope_id: str


class Situation(Strict):
    situation_id: str
    version: int = 1
    participant_ids: list[str]
    message_ids: list[str]
    event_refs: list[str]
    relation_refs: list[str]
    active_request_refs: list[str]
    conflicting_refs: list[str] = []
    unknown_information: list[str] = []
    object_types: list[str] = []
    condition_refs: list[str] = []
    reported_state_refs: list[str] = []
    verification_report_refs: list[str] = []
    mechanism_refs: list[str] = []


class Hypothesis(Strict):
    hypothesis_id: str
    scope_id: str
    description: str
    supporting_refs: list[str]
    conflicting_refs: list[str] = []
    missing_information: list[str] = []
    status: Literal['supported','possible','undetermined','not_supported']
    rule_id: str


class Consequence(Strict):
    consequence_id: str
    scope_id: str
    category: Literal['money','assets','personal_data','account_access','device_access','freedom','physical_safety']
    description: str
    action_refs: list[str]
    condition_refs: list[str]
    evidence_refs: list[str]
    information_status: Literal['inferred'] = 'inferred'
    rule_id: str


class Interpretation(Strict):
    reasoning_version: str = 'local-situation-1.0'
    behaviors: list[Behavior]
    situations: list[Situation]
    hypotheses: list[Hypothesis]
    consequences: list[Consequence]
    stage_timings_ms: dict[str,float] = {}
    limitations: list[str] = []
    clause_roles: list['ClauseRole'] = []
    salient_actions: list['SalientAction'] = []
    mechanisms: list['RiskMechanism'] = []


class RiskMechanism(Strict):
    mechanism_id: str
    situation_id: str
    risk_status: Literal['high','suspicious']
    action_refs: list[str]
    relation_refs: list[str]
    evidence_refs: list[str]
    affected_party_id: str
    asset_or_right: str
    summary: str
    recommended_action: str
    limitations: list[str] = []


class ClauseRole(Strict):
    clause_id: str
    scope_id: str
    evidence_refs: list[str]
    requester_id: str | None = None
    performer_id: str | None = None
    affected_party_id: str | None = None
    affected_role: str = 'unknown'
    affected_status: Literal['textual_role','unknown'] = 'unknown'
    unresolved_roles: list[str] = []
    event_refs: list[str] = []
    role_labels: dict[str,str] = {}


class SalientAction(Strict):
    scope_id: str
    event_refs: list[str]
    supporting_relation_refs: list[str]
    affected_party_id: str | None
    consequence: str
    selection_reason: str
    rule_id: str
    is_primary: bool = False


Interpretation.model_rebuild()
