"""Training-ready annotation container. Auto labels always require human review."""
from typing import Literal
from pydantic import Field
from ..schemas import Strict, AnalyzeRequest
from .schema import Participant, Span, Event, Relation, Answers18


class Annotation(Strict):
    participants: list[Participant]
    spans: list[Span]
    events: list[Event]
    relations: list[Relation]
    expected_answers_18: Answers18


class Provenance(Strict):
    source_split: Literal['dev', 'new_synthetic']
    source_id: str
    label_method: Literal['weak_label', 'human_annotation']
    rules_version: str | None
    rule_ids: list[str]


class AnnotatedSample(Strict):
    id: str
    schema_version: Literal['local-annotation-1.0'] = 'local-annotation-1.0'
    input: AnalyzeRequest
    annotations: Annotation
    risk_label_reference: Literal['clear','need_context','suspicious','high'] | None = None
    provenance: Provenance
    review_status: Literal['weak_label', 'pending_review', 'reviewed']
    reviewers: list[str] = Field(default_factory=list)

    # A downstream training job must select reviewed samples explicitly. Exporting
    # a weak label never turns it into a gold label or a final-risk prediction.
