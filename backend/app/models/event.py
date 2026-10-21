"""ORM models backing the Eventora persistence layer."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return uuid.uuid4().hex


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    event_type: Mapped[str] = mapped_column(String(48), nullable=False, default="wedding")
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    city: Mapped[str] = mapped_column(String(96), nullable=False, default="metro")
    guest_count: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    budget: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    theme: Mapped[str] = mapped_column(String(64), nullable=False, default="Elegant")
    style: Mapped[str] = mapped_column(String(48), nullable=False, default="Classic")
    preferences: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    # Cost-model drivers
    venue_type: Mapped[str] = mapped_column(String(48), nullable=False, default="banquet_hall")
    duration_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    catering_level: Mapped[str] = mapped_column(String(32), nullable=False, default="standard")
    decoration_level: Mapped[str] = mapped_column(String(32), nullable=False, default="standard")
    photography: Mapped[str] = mapped_column(String(32), nullable=False, default="standard")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    plan: Mapped["EventPlan | None"] = relationship(
        back_populates="event", cascade="all, delete-orphan", uselist=False
    )
    checklist_items: Mapped[list["ChecklistItem"]] = relationship(
        back_populates="event", cascade="all, delete-orphan", order_by="ChecklistItem.sort_order"
    )
    timeline_items: Mapped[list["TimelineItem"]] = relationship(
        back_populates="event", cascade="all, delete-orphan", order_by="TimelineItem.sort_order"
    )
    expenses: Mapped[list["Expense"]] = relationship(
        back_populates="event", cascade="all, delete-orphan", order_by="Expense.sort_order"
    )


class EventPlan(Base):
    __tablename__ = "event_plans"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    event_id: Mapped[str] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="fallback")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    event: Mapped["Event"] = relationship(back_populates="plan")


class ChecklistItem(Base):
    __tablename__ = "checklist_items"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    event_id: Mapped[str] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(48), nullable=False, default="General")
    item: Mapped[str] = mapped_column(String(200), nullable=False)
    vendor_type: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    estimated_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    actual_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    event: Mapped["Event"] = relationship(back_populates="checklist_items")


class TimelineItem(Base):
    __tablename__ = "timeline_items"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    event_id: Mapped[str] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    phase: Mapped[str] = mapped_column(String(32), nullable=False, default="preparation")
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    day_offset: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    owner: Mapped[str] = mapped_column(String(64), nullable=False, default="You")
    done: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    event: Mapped["Event"] = relationship(back_populates="timeline_items")


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    event_id: Mapped[str] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(48), nullable=False, default="General")
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    estimated: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    actual: Mapped[float | None] = mapped_column(Float, nullable=True)
    paid: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    event: Mapped["Event"] = relationship(back_populates="expenses")
