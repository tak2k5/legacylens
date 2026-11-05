"""Output contracts. Every claim about the code carries a citation that a script can check."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

RuleKind = Literal["validation", "calculation", "routing", "data-access", "error-handling", "authorization", "other"]


class Citation(BaseModel):
    program: str = Field(description="Program id, for example CBTRN02C")
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)

    @field_validator("program")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("end_line")
    @classmethod
    def _order(cls, v: int, info) -> int:
        start = info.data.get("start_line")
        if start is not None and v < start:
            raise ValueError("end_line must be >= start_line")
        return v


class BusinessRule(BaseModel):
    id: str = Field(description="Stable id, for example CBTRN02C-R1")
    program: str
    paragraph: str | None = None
    kind: RuleKind
    summary: str = Field(description="One sentence a new engineer can understand, no COBOL jargon")
    condition: str | None = Field(default=None, description="When the rule fires, in plain words")
    outcome: str | None = Field(default=None, description="What happens, including codes or messages")
    fields: list[str] = Field(default_factory=list, description="COBOL data names the rule reads or sets")
    citations: list[Citation] = Field(min_length=1)

    @field_validator("program")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.strip().upper()


class RuleSet(BaseModel):
    program: str
    purpose: str = Field(description="Two sentences: what the program does for the business")
    rules: list[BusinessRule]


class Answer(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
