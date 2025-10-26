from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RuleDefinitionSchema(BaseModel):
    id: str
    name: str
    scope: str
    description: str | None = None
    when: dict[str, Any]
    then: dict[str, Any]
    disabled: bool = False

    model_config = ConfigDict(extra="ignore")


class RuleSetContent(BaseModel):
    yaml: str
    rules: list[RuleDefinitionSchema]
    metadata: dict[str, Any] = Field(default_factory=dict)


class RuleSetRead(BaseModel):
    id: int
    name: str
    version: str
    is_global: bool
    created_at: datetime
    content: RuleSetContent

    model_config = ConfigDict(from_attributes=True)


class RuleSetUpsert(BaseModel):
    yaml: str
    name: str | None = None
    version: str | None = None


class RuleEditorPayload(BaseModel):
    baseline: RuleSetRead
    override: RuleSetRead | None = None
    effective_yaml: str
    effective_rules: list[RuleDefinitionSchema]
    metadata: dict[str, Any] = Field(default_factory=dict)


class RulePackRead(BaseModel):
    slug: str
    name: str
    description: str | None = None
    version: str | None = None
    yaml: str
