"""Structured schema for the AI-generated event plan.

The plan is validated with Pydantic so that a malformed model response can
never corrupt the database or crash the API. If validation fails, the caller
falls back to the deterministic planner.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.vocabulary import (
    CATERING_LEVELS,
    DECORATION_LEVELS,
    EVENT_TYPES,
    PHOTOGRAPHY_LEVELS,
    STYLES,
    THEMES,
    VENUE_TYPES,
)


class PlanOverview(BaseModel):
    concept: str = Field(..., min_length=10, max_length=600)
    theme: str = Field(..., max_length=64)
    style: str = Field(..., max_length=48)
    color_palette: list[str] = Field(default_factory=list, max_length=8)
    highlights: list[str] = Field(default_factory=list, max_length=10)


class PlanBudgetLine(BaseModel):
    category: str = Field(..., min_length=1, max_length=48)
    description: str = Field(..., min_length=1, max_length=200)
    estimated_cost: float = Field(..., ge=0)
    priority: Literal["must_have", "should_have", "nice_to_have"] = "should_have"

    @field_validator("category")
    @classmethod
    def _trim(cls, v: str) -> str:
        return v.strip()


class PlanChecklistItem(BaseModel):
    category: str = Field(..., min_length=1, max_length=48)
    item: str = Field(..., min_length=1, max_length=200)
    vendor_type: str = Field(default="", max_length=64)
    notes: str = Field(default="", max_length=500)
    estimated_cost: float = Field(default=0.0, ge=0)


class PlanTimelineItem(BaseModel):
    phase: Literal["preparation", "event_day"] = "preparation"
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=500)
    day_offset: int = Field(..., ge=-365, le=365)
    owner: str = Field(default="You", max_length=64)


class PlanScheduleSlot(BaseModel):
    start_time: str = Field(..., min_length=4, max_length=10)
    end_time: str = Field(..., min_length=4, max_length=10)
    activity: str = Field(..., min_length=1, max_length=200)
    notes: str = Field(default="", max_length=500)

    @field_validator("start_time", "end_time")
    @classmethod
    def _time_format(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("time must not be empty")
        return v


class EventPlanSchema(BaseModel):
    """Full structured plan returned by the AI layer."""

    overview: PlanOverview
    budget_breakdown: list[PlanBudgetLine] = Field(default_factory=list, max_length=20)
    checklist: list[PlanChecklistItem] = Field(default_factory=list, max_length=60)
    timeline: list[PlanTimelineItem] = Field(default_factory=list, max_length=40)
    event_day_schedule: list[PlanScheduleSlot] = Field(default_factory=list, max_length=40)
    tips: list[str] = Field(default_factory=list, max_length=12)
    contingency_note: str = Field(default="", max_length=500)
    assumptions: list[str] = Field(default_factory=list, max_length=12)

    @field_validator("overview")
    @classmethod
    def _validate_overview(cls, v: PlanOverview) -> PlanOverview:
        if v.theme not in THEMES:
            v.theme = THEMES[0]
        if v.style not in STYLES:
            v.style = STYLES[0]
        return v

    @field_validator("budget_breakdown")
    @classmethod
    def _validate_budget(cls, v: list[PlanBudgetLine]) -> list[PlanBudgetLine]:
        for line in v:
            if line.estimated_cost < 0:
                line.estimated_cost = 0.0
        return v

    def to_payload(self) -> dict:
        return self.model_dump()
