"""Event CRUD routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories import event_repo
from app.schemas.event import (
    EventCreate,
    EventDetailOut,
    EventOut,
    EventUpdate,
)

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=list[EventOut])
def list_events(db: Session = Depends(get_db)) -> list[EventOut]:
    return [EventOut.model_validate(event_repo._event_to_dict(e)) for e in event_repo.list_events(db)]


@router.post("", response_model=EventOut, status_code=status.HTTP_201_CREATED)
def create_event(payload: EventCreate, db: Session = Depends(get_db)) -> EventOut:
    event = event_repo.create_event(db, payload.model_dump())
    return EventOut.model_validate(event_repo._event_to_dict(event))


@router.get("/{event_id}", response_model=EventDetailOut)
def get_event(event_id: str, db: Session = Depends(get_db)) -> EventDetailOut:
    event = event_repo.get_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found.")

    data = event_repo._event_to_dict(event)
    plan_record = event_repo.get_plan(db, event_id)
    data["plan"] = event_repo.plan_content(plan_record)
    data["plan_source"] = plan_record.source if plan_record else None
    data["checklist"] = [event_repo._event_to_dict_checklist(i) for i in event_repo.list_checklist(db, event_id)]
    data["timeline"] = [event_repo._event_to_dict_timeline(i) for i in event_repo.list_timeline(db, event_id)]
    data["expenses"] = [event_repo._event_to_dict_expense(i) for i in event_repo.list_expenses(db, event_id)]
    return EventDetailOut.model_validate(data)


@router.patch("/{event_id}", response_model=EventOut)
def update_event(
    event_id: str, payload: EventUpdate, db: Session = Depends(get_db)
) -> EventOut:
    event = event_repo.get_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found.")
    changes = payload.applied()
    if not changes:
        return EventOut.model_validate(event_repo._event_to_dict(event))
    updated = event_repo.update_event(db, event, changes)
    return EventOut.model_validate(event_repo._event_to_dict(updated))


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: str, db: Session = Depends(get_db)) -> None:
    event = event_repo.get_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found.")
    event_repo.delete_event(db, event)
