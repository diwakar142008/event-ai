"""Repository layer — all database access lives here.

Routers never touch SQLAlchemy models directly; they call these functions.
This keeps the persistence logic testable and swappable (SQLite -> Postgres).
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ChecklistItem, Event, EventPlan, Expense, TimelineItem


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _prefs_to_list(raw: str) -> list[str]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []
    return [str(p) for p in parsed] if isinstance(parsed, list) else []


def _event_to_dict(event: Event) -> dict[str, Any]:
    return {
        "id": event.id,
        "name": event.name,
        "event_type": event.event_type,
        "event_date": event.event_date,
        "city": event.city,
        "guest_count": event.guest_count,
        "budget": event.budget,
        "theme": event.theme,
        "style": event.style,
        "preferences": _prefs_to_list(event.preferences),
        "venue_type": event.venue_type,
        "duration_hours": event.duration_hours,
        "catering_level": event.catering_level,
        "decoration_level": event.decoration_level,
        "photography": event.photography,
        "created_at": event.created_at,
        "updated_at": event.updated_at,
    }


# --------------------------------------------------------------------------- #
# Events
# --------------------------------------------------------------------------- #
def list_events(db: Session) -> list[Event]:
    stmt = select(Event).order_by(Event.event_date.asc(), Event.created_at.asc())
    return list(db.execute(stmt).scalars().all())


def get_event(db: Session, event_id: str) -> Event | None:
    return db.get(Event, event_id)


def create_event(db: Session, payload: dict[str, Any]) -> Event:
    data = dict(payload)
    data["preferences"] = json.dumps(data.get("preferences", []))
    if isinstance(data.get("event_date"), date):
        data["event_date"] = data["event_date"]
    event = Event(**data)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def update_event(db: Session, event: Event, changes: dict[str, Any]) -> Event:
    for key, value in changes.items():
        if key == "preferences":
            value = json.dumps(value)
        setattr(event, key, value)
    event.updated_at = _utcnow()
    db.commit()
    db.refresh(event)
    return event


def delete_event(db: Session, event: Event) -> None:
    db.delete(event)
    db.commit()


# --------------------------------------------------------------------------- #
# Plans
# --------------------------------------------------------------------------- #
def get_plan(db: Session, event_id: str) -> EventPlan | None:
    stmt = select(EventPlan).where(EventPlan.event_id == event_id)
    return db.execute(stmt).scalars().first()


def save_plan(db: Session, event_id: str, plan: dict[str, Any], source: str) -> EventPlan:
    record = get_plan(db, event_id)
    content = json.dumps(plan, default=str)
    if record is None:
        record = EventPlan(event_id=event_id, content=content, source=source)
        db.add(record)
    else:
        record.content = content
        record.source = source
    db.commit()
    db.refresh(record)
    return record


def plan_content(record: EventPlan | None) -> dict[str, Any] | None:
    if record is None:
        return None
    try:
        parsed = json.loads(record.content)
    except (json.JSONDecodeError, TypeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _event_to_dict_checklist(item: ChecklistItem) -> dict[str, Any]:
    return {
        "id": item.id,
        "category": item.category,
        "item": item.item,
        "vendor_type": item.vendor_type,
        "status": item.status,
        "notes": item.notes,
        "estimated_cost": item.estimated_cost,
        "actual_cost": item.actual_cost,
    }


def _event_to_dict_timeline(item: TimelineItem) -> dict[str, Any]:
    return {
        "id": item.id,
        "phase": item.phase,
        "title": item.title,
        "description": item.description,
        "day_offset": item.day_offset,
        "owner": item.owner,
        "done": bool(item.done),
    }


def _event_to_dict_expense(item: Expense) -> dict[str, Any]:
    return {
        "id": item.id,
        "category": item.category,
        "description": item.description,
        "estimated": item.estimated,
        "actual": item.actual,
        "paid": bool(item.paid),
    }



# --------------------------------------------------------------------------- #
# Checklist
# --------------------------------------------------------------------------- #
def list_checklist(db: Session, event_id: str) -> list[ChecklistItem]:
    stmt = (
        select(ChecklistItem)
        .where(ChecklistItem.event_id == event_id)
        .order_by(ChecklistItem.sort_order.asc(), ChecklistItem.id.asc())
    )
    return list(db.execute(stmt).scalars().all())


def add_checklist_item(
    db: Session, event_id: str, payload: dict[str, Any]
) -> ChecklistItem:
    next_order = len(list_checklist(db, event_id))
    item = ChecklistItem(event_id=event_id, sort_order=next_order, **payload)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_checklist_item(db: Session, item_id: str) -> ChecklistItem | None:
    return db.get(ChecklistItem, item_id)


def update_checklist_item(
    db: Session, item: ChecklistItem, changes: dict[str, Any]
) -> ChecklistItem:
    for key, value in changes.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


def delete_checklist_item(db: Session, item: ChecklistItem) -> None:
    db.delete(item)
    db.commit()


# --------------------------------------------------------------------------- #
# Timeline
# --------------------------------------------------------------------------- #
def list_timeline(db: Session, event_id: str) -> list[TimelineItem]:
    stmt = (
        select(TimelineItem)
        .where(TimelineItem.event_id == event_id)
        .order_by(TimelineItem.sort_order.asc(), TimelineItem.day_offset.asc())
    )
    return list(db.execute(stmt).scalars().all())


def add_timeline_item(db: Session, event_id: str, payload: dict[str, Any]) -> TimelineItem:
    next_order = len(list_timeline(db, event_id))
    item = TimelineItem(event_id=event_id, sort_order=next_order, **payload)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_timeline_item(db: Session, item_id: str) -> TimelineItem | None:
    return db.get(TimelineItem, item_id)


def update_timeline_item(
    db: Session, item: TimelineItem, changes: dict[str, Any]
) -> TimelineItem:
    for key, value in changes.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


def delete_timeline_item(db: Session, item: TimelineItem) -> None:
    db.delete(item)
    db.commit()


# --------------------------------------------------------------------------- #
# Expenses
# --------------------------------------------------------------------------- #
def list_expenses(db: Session, event_id: str) -> list[Expense]:
    stmt = (
        select(Expense)
        .where(Expense.event_id == event_id)
        .order_by(Expense.sort_order.asc(), Expense.id.asc())
    )
    return list(db.execute(stmt).scalars().all())


def add_expense(db: Session, event_id: str, payload: dict[str, Any]) -> Expense:
    next_order = len(list_expenses(db, event_id))
    item = Expense(event_id=event_id, sort_order=next_order, **payload)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_expense(db: Session, expense_id: str) -> Expense | None:
    return db.get(Expense, expense_id)


def update_expense(db: Session, expense: Expense, changes: dict[str, Any]) -> Expense:
    for key, value in changes.items():
        setattr(expense, key, value)
    db.commit()
    db.refresh(expense)
    return expense


def delete_expense(db: Session, expense: Expense) -> None:
    db.delete(expense)
    db.commit()


def replace_event_workspace(
    db: Session,
    event_id: str,
    checklist: list[dict[str, Any]],
    timeline: list[dict[str, Any]],
    expenses: list[dict[str, Any]],
) -> None:
    """Replace the whole working set for an event in one transaction.

    Used when a freshly generated plan is applied to an event so the checklist,
    timeline and budget lines stay consistent with each other.
    """
    for model in (ChecklistItem, TimelineItem, Expense):
        for row in db.execute(
            select(model).where(model.event_id == event_id)
        ).scalars().all():
            db.delete(row)
    db.flush()

    for index, item in enumerate(checklist):
        db.add(
            ChecklistItem(
                event_id=event_id,
                category=item.get("category", "General"),
                item=item.get("item", ""),
                vendor_type=item.get("vendor_type", ""),
                status=item.get("status", "pending"),
                notes=item.get("notes", ""),
                estimated_cost=float(item.get("estimated_cost", 0) or 0),
                actual_cost=item.get("actual_cost"),
                sort_order=index,
            )
        )
    for index, item in enumerate(timeline):
        db.add(
            TimelineItem(
                event_id=event_id,
                phase=item.get("phase", "preparation"),
                title=item.get("title", ""),
                description=item.get("description", ""),
                day_offset=int(item.get("day_offset", 0) or 0),
                owner=item.get("owner", "You"),
                done=1 if item.get("done") else 0,
                sort_order=index,
            )
        )
    for index, item in enumerate(expenses):
        db.add(
            Expense(
                event_id=event_id,
                category=item.get("category", "General"),
                description=item.get("description", ""),
                estimated=float(item.get("estimated", 0) or 0),
                actual=item.get("actual"),
                paid=1 if item.get("paid") else 0,
                sort_order=index,
            )
        )
    db.commit()
