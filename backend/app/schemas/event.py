"""Pydantic request/response schemas for the Eventora API."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.vocabulary import (
    CATERING_LEVELS,
    CITY_TIERS,
    DECORATION_LEVELS,
    DURATION_HOURS,
    EVENT_TYPES,
    PHOTOGRAPHY_LEVELS,
    STYLES,
    THEMES,
    VENUE_TYPES,
)

# --------------------------------------------------------------------------- #
# Event schemas
# --------------------------------------------------------------------------- #
class EventBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=160)
    event_type: str = Field(..., max_length=48)
    event_date: date
    city: str = Field(..., max_length=96)
    guest_count: int = Field(..., ge=1, le=2000)
    budget: float = Field(..., ge=0, le=100_000_000)
    theme: str = Field(..., max_length=64)
    style: str = Field(..., max_length=48)
    preferences: list[str] = Field(default_factory=list, max_length=20)
    venue_type: str = Field(..., max_length=48)
    duration_hours: int = Field(...)
    catering_level: str = Field(..., max_length=32)
    decoration_level: str = Field(..., max_length=32)
    photography: str = Field(..., max_length=32)

    @field_validator("event_type")
    @classmethod
    def _check_event_type(cls, v: str) -> str:
        if v not in EVENT_TYPES:
            raise ValueError(f"event_type must be one of {EVENT_TYPES}")
        return v

    @field_validator("city")
    @classmethod
    def _check_city(cls, v: str) -> str:
        if v not in CITY_TIERS:
            raise ValueError(f"city must be one of {CITY_TIERS}")
        return v

    @field_validator("venue_type")
    @classmethod
    def _check_venue(cls, v: str) -> str:
        if v not in VENUE_TYPES:
            raise ValueError(f"venue_type must be one of {VENUE_TYPES}")
        return v

    @field_validator("duration_hours")
    @classmethod
    def _check_duration(cls, v: int) -> int:
        if v not in DURATION_HOURS:
            raise ValueError(f"duration_hours must be one of {DURATION_HOURS}")
        return v

    @field_validator("catering_level")
    @classmethod
    def _check_catering(cls, v: str) -> str:
        if v not in CATERING_LEVELS:
            raise ValueError(f"catering_level must be one of {CATERING_LEVELS}")
        return v

    @field_validator("decoration_level")
    @classmethod
    def _check_decoration(cls, v: str) -> str:
        if v not in DECORATION_LEVELS:
            raise ValueError(f"decoration_level must be one of {DECORATION_LEVELS}")
        return v

    @field_validator("photography")
    @classmethod
    def _check_photography(cls, v: str) -> str:
        if v not in PHOTOGRAPHY_LEVELS:
            raise ValueError(f"photography must be one of {PHOTOGRAPHY_LEVELS}")
        return v

    @field_validator("style")
    @classmethod
    def _check_style(cls, v: str) -> str:
        if v not in STYLES:
            raise ValueError(f"style must be one of {STYLES}")
        return v

    @field_validator("theme")
    @classmethod
    def _check_theme(cls, v: str) -> str:
        if v not in THEMES:
            raise ValueError(f"theme must be one of {THEMES}")
        return v

    @field_validator("preferences")
    @classmethod
    def _clean_preferences(cls, v: list[str]) -> list[str]:
        return [str(item).strip()[:80] for item in v if str(item).strip()]


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    """All fields optional — supports partial updates from the edit drawer."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=2, max_length=160)
    event_type: str | None = None
    event_date: date | None = None
    city: str | None = None
    guest_count: int | None = Field(default=None, ge=1, le=2000)
    budget: float | None = Field(default=None, ge=0, le=100_000_000)
    theme: str | None = None
    style: str | None = None
    preferences: list[str] | None = None
    venue_type: str | None = None
    duration_hours: int | None = None
    catering_level: str | None = None
    decoration_level: str | None = None
    photography: str | None = None

    def applied(self) -> dict[str, Any]:
        return {k: v for k, v in self.model_dump(exclude_unset=True).items() if v is not None}


class ChecklistItemCreate(BaseModel):
    category: str = Field(default="General", max_length=48)
    item: str = Field(..., min_length=1, max_length=200)
    vendor_type: str = Field(default="", max_length=64)
    notes: str = Field(default="", max_length=1000)
    estimated_cost: float = Field(default=0.0, ge=0)


class ChecklistItemUpdate(BaseModel):
    status: Literal["pending", "contacted", "booked", "completed", "skipped"] | None = None
    notes: str | None = Field(default=None, max_length=1000)
    estimated_cost: float | None = Field(default=None, ge=0)
    actual_cost: float | None = Field(default=None, ge=0)
    item: str | None = Field(default=None, min_length=1, max_length=200)
    category: str | None = Field(default=None, max_length=48)
    vendor_type: str | None = Field(default=None, max_length=64)


class ChecklistItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    category: str
    item: str
    vendor_type: str
    status: str
    notes: str
    estimated_cost: float
    actual_cost: float | None


class TimelineItemCreate(BaseModel):
    phase: Literal["preparation", "event_day"] = "preparation"
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    day_offset: int = Field(..., ge=-365, le=365)
    owner: str = Field(default="You", max_length=64)


class TimelineItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    day_offset: int | None = Field(default=None, ge=-365, le=365)
    owner: str | None = Field(default=None, max_length=64)
    done: bool | None = None


class TimelineItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    phase: str
    title: str
    description: str
    day_offset: int
    owner: str
    done: bool


class ExpenseCreate(BaseModel):
    category: str = Field(default="General", max_length=48)
    description: str = Field(..., min_length=1, max_length=200)
    estimated: float = Field(default=0.0, ge=0)
    actual: float | None = Field(default=None, ge=0)


class ExpenseUpdate(BaseModel):
    category: str | None = Field(default=None, max_length=48)
    description: str | None = Field(default=None, min_length=1, max_length=200)
    estimated: float | None = Field(default=None, ge=0)
    actual: float | None = Field(default=None, ge=0)
    paid: bool | None = None


class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    category: str
    description: str
    estimated: float
    actual: float | None
    paid: bool


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    event_type: str
    event_date: date
    city: str
    guest_count: int
    budget: float
    theme: str
    style: str
    preferences: list[str]
    venue_type: str
    duration_hours: int
    catering_level: str
    decoration_level: str
    photography: str
    created_at: datetime
    updated_at: datetime


class EventDetailOut(EventOut):
    plan: dict[str, Any] | None = None
    plan_source: str | None = None
    checklist: list[ChecklistItemOut] = Field(default_factory=list)
    timeline: list[TimelineItemOut] = Field(default_factory=list)
    expenses: list[ExpenseOut] = Field(default_factory=list)




# --------------------------------------------------------------------------- #
# ML schemas
# --------------------------------------------------------------------------- #
class CostPredictionRequest(BaseModel):
    event_type: str
    guest_count: int = Field(..., ge=1, le=2000)
    city: str
    venue_type: str
    duration_hours: int
    catering_level: str
    decoration_level: str
    photography: str
    budget: float | None = Field(default=None, ge=0)

    @field_validator("event_type")
    @classmethod
    def _check_event_type(cls, v: str) -> str:
        if v not in EVENT_TYPES:
            raise ValueError(f"event_type must be one of {EVENT_TYPES}")
        return v

    @field_validator("city")
    @classmethod
    def _check_city(cls, v: str) -> str:
        if v not in CITY_TIERS:
            raise ValueError(f"city must be one of {CITY_TIERS}")
        return v

    @field_validator("venue_type")
    @classmethod
    def _check_venue(cls, v: str) -> str:
        if v not in VENUE_TYPES:
            raise ValueError(f"venue_type must be one of {VENUE_TYPES}")
        return v

    @field_validator("duration_hours")
    @classmethod
    def _check_duration(cls, v: int) -> int:
        if v not in DURATION_HOURS:
            raise ValueError(f"duration_hours must be one of {DURATION_HOURS}")
        return v

    @field_validator("catering_level")
    @classmethod
    def _check_catering(cls, v: str) -> str:
        if v not in CATERING_LEVELS:
            raise ValueError(f"catering_level must be one of {CATERING_LEVELS}")
        return v

    @field_validator("decoration_level")
    @classmethod
    def _check_decoration(cls, v: str) -> str:
        if v not in DECORATION_LEVELS:
            raise ValueError(f"decoration_level must be one of {DECORATION_LEVELS}")
        return v

    @field_validator("photography")
    @classmethod
    def _check_photography(cls, v: str) -> str:
        if v not in PHOTOGRAPHY_LEVELS:
            raise ValueError(f"photography must be one of {PHOTOGRAPHY_LEVELS}")
        return v


class CostPredictionOut(BaseModel):
    predicted_cost: float
    currency: str
    lower_bound: float
    upper_bound: float
    per_guest_cost: float
    confidence_note: str
    budget: float | None = None
    budget_gap: float | None = None
    budget_status: Literal["within_budget", "over_budget", "no_budget"] = "no_budget"
    budget_usage_pct: float | None = None
    feature_importances: dict[str, float] = Field(default_factory=dict)
    data_note: str


class RecommendationRequest(BaseModel):
    event_type: str
    budget: float = Field(..., ge=0)
    guest_count: int = Field(..., ge=1, le=2000)
    preferences: list[str] = Field(default_factory=list, max_length=20)
    style: str = Field(default="Classic", max_length=48)
    top_k: int = Field(default=8, ge=1, le=25)

    @field_validator("event_type")
    @classmethod
    def _check_event_type(cls, v: str) -> str:
        if v not in EVENT_TYPES:
            raise ValueError(f"event_type must be one of {EVENT_TYPES}")
        return v

    @field_validator("style")
    @classmethod
    def _check_style(cls, v: str) -> str:
        if v not in STYLES:
            raise ValueError(f"style must be one of {STYLES}")
        return v


class RecommendationItem(BaseModel):
    rank: int
    name: str
    category: str
    score: float
    reason: str
    tags: list[str] = Field(default_factory=list)
    estimated_cost_per_guest: float | None = None


class RecommendationOut(BaseModel):
    recommendations: list[RecommendationItem]
    explanation: str
    method_note: str


class BudgetRiskRequest(BaseModel):
    budget: float = Field(..., ge=0)
    predicted_cost: float = Field(..., ge=0)
    contingency_pct: float = Field(default=10.0, ge=0, le=100)
    guest_count: int = Field(..., ge=1, le=2000)


class BudgetRiskOut(BaseModel):
    risk_level: Literal["low", "medium", "high"]
    risk_label: str
    confidence: float
    reasons: list[str]
    suggested_contingency: float
    recommended_contingency_pct: float
    saving_tips: list[str]
    assumptions: list[str]
    method_note: str


class MLMetricsOut(BaseModel):
    cost_model: dict[str, Any]
    recommendation_model: dict[str, Any]
    risk_model: dict[str, Any]
    generated_at: str
    dataset_note: str


# --------------------------------------------------------------------------- #
# AI schemas
# --------------------------------------------------------------------------- #
class GeneratePlanRequest(BaseModel):
    event_id: str | None = None
    event: EventCreate | None = None
    extra_instructions: str = Field(default="", max_length=2000)
    regenerate: bool = False


class GeneratePlanOut(BaseModel):
    plan: dict[str, Any]
    source: Literal["ai", "fallback"]
    provider: str
    model: str
    notice: str


class ChatRequest(BaseModel):
    event_id: str | None = None
    message: str = Field(..., min_length=1, max_length=4000)
    history: list[dict[str, str]] = Field(default_factory=list, max_length=40)


class ChatOut(BaseModel):
    reply: str
    source: Literal["ai", "fallback"]
    provider: str
    model: str
    notice: str


class HealthOut(BaseModel):
    status: str
    version: str
    environment: str
    ai_provider: str
    ai_configured: bool
    database: str
    models_loaded: dict[str, bool]
    timestamp: str


class ErrorOut(BaseModel):
    error: str
    message: str
    details: Any | None = None
