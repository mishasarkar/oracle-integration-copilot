from typing import Literal, Optional
from pydantic import BaseModel, Field


class IntegrationIntent(BaseModel):
    pattern: Literal["scheduled", "event_driven", "request_response", "file_based"]
    source_system: str
    target_system: str
    objects: list[str]
    schedule: Optional[str] = None
    filters: list[str] = Field(default_factory=list)
    notifications: list[str] = Field(default_factory=list)
    raw_requirement: str


class FieldMapping(BaseModel):
    source_field: str
    target_field: str
    transformation: Optional[str] = None
    required: bool
    notes: Optional[str] = None


class IntegrationSpec(BaseModel):
    title: str
    pattern: str
    source: dict
    target: dict
    mappings: list[FieldMapping]
    filters: list[str] = Field(default_factory=list)
    error_handling: list[str] = Field(default_factory=list)
    monitoring: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
