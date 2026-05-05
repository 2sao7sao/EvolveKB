from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class SourceDocument(StrictBaseModel):
    id: str
    uri: str
    source_type: Literal["markdown", "txt", "pdf", "url", "repo", "manual"]
    title: str | None = None
    author: str | None = None
    created_at: datetime | None = None
    ingested_at: datetime
    content_hash: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class SourceChunk(StrictBaseModel):
    id: str
    source_id: str
    chunk_index: int
    heading_path: list[str] = Field(default_factory=list)
    text: str
    token_count: int
    char_start: int | None = None
    char_end: int | None = None
    embedding_text: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class Claim(StrictBaseModel):
    id: str
    source_id: str
    chunk_ids: list[str] = Field(default_factory=list)
    text: str
    normalized_subject: str | None = None
    normalized_predicate: str | None = None
    normalized_object: str | None = None
    claim_type: Literal[
        "fact", "definition", "principle", "procedure", "constraint", "tradeoff", "example"
    ]
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_quote: str
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    status: Literal["active", "conflicting", "superseded", "rejected"] = "active"
    metadata: dict[str, Any] = Field(default_factory=dict)


class Concept(StrictBaseModel):
    id: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    description: str = ""
    related_claim_ids: list[str] = Field(default_factory=list)
    related_knowledge_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class KnowledgeBlock(StrictBaseModel):
    schema_version: int = 2
    id: str
    name: str
    kind: Literal["knowledge"] = "knowledge"
    block_type: Literal["concept", "pattern", "decision", "procedure", "case", "reference"]
    summary: str
    source_refs: list[dict[str, Any]] = Field(default_factory=list)
    claims: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    chunk_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    updated_at: date
    version: int = Field(default=1, ge=1)
    supersedes: str | None = None
    tags: list[str] = Field(default_factory=list)
    recommended_usage: list[str] = Field(default_factory=list)
    status: Literal["active", "conflicting", "superseded", "rejected"] = "active"
    metadata: dict[str, Any] = Field(default_factory=dict)


class UsageAsset(StrictBaseModel):
    schema_version: int = 2
    id: str
    name: str
    kind: Literal["usage"] = "usage"
    intent: str
    strategy: Literal["reference", "digest", "transform", "evolve", "playbook", "procedure", "checklist"]
    pattern: Literal["required", "optional", "not_needed", "TBD"]
    uses: list[str] = Field(default_factory=list)
    playbook: str | None = None
    steps: list[str] = Field(default_factory=list)
    trigger_examples: list[str] = Field(default_factory=list)
    anti_trigger_examples: list[str] = Field(default_factory=list)
    gate_policy_ids: list[str] = Field(default_factory=list)
    eval_case_ids: list[str] = Field(default_factory=list)
    updated_at: date
    needs_review: bool = False


class SkillAsset(StrictBaseModel):
    schema_version: int = 2
    name: str
    description: str
    kind: Literal["playbook", "procedure"]
    intent: str | None = None
    inputs_schema: dict[str, Any] = Field(default_factory=dict)
    outputs_schema: dict[str, Any] = Field(default_factory=dict)
    steps: list[dict[str, Any]] = Field(default_factory=list)
    preconditions: list[str] = Field(default_factory=list)
    postconditions: list[str] = Field(default_factory=list)
    allowed_tools: list[str] = Field(default_factory=list)
    supporting_files: list[str] = Field(default_factory=list)
    examples: list[dict[str, Any]] = Field(default_factory=list)
    version: str = "0.2.0"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("description must be non-empty")
        return value


class GatePolicy(StrictBaseModel):
    schema_version: int = 2
    id: str
    name: str
    kind: Literal["gate_policy"] = "gate_policy"
    scope: Literal["knowledge", "usage", "skill", "proposal", "output", "runtime"]
    level: int = Field(ge=0, le=3)
    checks: list[dict[str, Any]] = Field(default_factory=list)
    failure_action: Literal["warn", "block", "review_required"]
    updated_at: date


class Proposal(StrictBaseModel):
    schema_version: int = 2
    id: str
    title: str
    proposal_type: Literal[
        "knowledge_update", "usage_update", "skill_update", "gate_update", "settings_update"
    ]
    status: Literal["draft", "pending_review", "approved", "rejected", "applied", "rolled_back"]
    rationale: str
    impacted_assets: list[str] = Field(default_factory=list)
    before_hashes: dict[str, str] = Field(default_factory=dict)
    after_patches: list[dict[str, Any]] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    eval_results: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    reviewed_at: datetime | None = None
    reviewer: str | None = None


class StepTrace(StrictBaseModel):
    step_index: int
    procedure: str
    input_hash: str
    output_hash: str
    started_at: datetime
    finished_at: datetime
    success: bool
    error: str | None = None
    gate_results: list[dict[str, Any]] = Field(default_factory=list)


class RunTrace(StrictBaseModel):
    schema_version: int = 2
    id: str
    intent: str
    mode: str
    question: str | None = None
    selected_skill: str | None = None
    retrieval_plan: dict[str, Any] = Field(default_factory=dict)
    retrieved_knowledge_ids: list[str] = Field(default_factory=list)
    step_traces: list[dict[str, Any]] = Field(default_factory=list)
    gate_results: list[dict[str, Any]] = Field(default_factory=list)
    output_hash: str
    created_at: datetime


class GateResult(StrictBaseModel):
    gate_id: str
    passed: bool
    severity: Literal["info", "warning", "error", "blocker"]
    score: float | None = None
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
