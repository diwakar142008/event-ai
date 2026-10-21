"""Checklist, timeline and expense routes — all scoped to an event."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories import event_repo
from app.schemas.event import (
    ChecklistItemCreate,
    ChecklistItemOut,
    ChecklistItemUpdate,
    ExpenseCreate,
    ExpenseOut,
    ExpenseUpdate,
    TimelineItemCreate,
    TimelineItemOut,
    TimelineItemUpdate,
)

router = APIRouter(prefix="/api/events/{event_id}", tags=["workspace"])


def _require_event(db: Session, event_id: str):
    event = event_repo.get_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found.")
    return event


# --------------------------------------------------------------------------- #
# Checklist
# --------------------------------------------------------------------------- #
@router.get("/checklist", response_model=list[ChecklistItemOut])
def get_checklist(event_id: str, db: Session = Depends(get_db)) -> list[ChecklistItemOut]:
    _require_event(db, event_id)
    return [
        ChecklistItemOut.model_validate(event_repo._event_to_dict_checklist(i))
        for i in event_repo.list_checklist(db, event_id)
    ]


@router.post("/checklist", response_model=ChecklistItemOut, status_code=status.HTTP_201_CREATED)
def add_checklist(
    event_id: str, payload: ChecklistItemCreate, db: Session = Depends(get_db)
) -> ChecklistItemOut:
    _require_event(db, event_id)
    item = event_repo.add_checklist_item(db, event_id, payload.model_dump())
    return ChecklistItemOut.model_validate(event_repo._event_to_dict_checklist(item))


@router.patch("/checklist/{item_id}", response_model=ChecklistItemOut)
def update_checklist(
    event_id: str,
    item_id: str,
    payload: ChecklistItemUpdate,
    db: Session = Depends(get_db),
) -> ChecklistItemOut:
    _require_event(db, event_id)
    item = event_repo.get_checklist_item(db, item_id)
    if item is None or item.event_id != event_id:
        raise HTTPException(status_code=404, detail="Checklist item not found.")
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    updated = event_repo.update_checklist_item(db, item, changes)
    return ChecklistItemOut.model_validate(event_repo._event_to_dict_checklist(updated))


# --------------------------------------------------------------------------- #
# Timeline
# --------------------------------------------------------------------------- #
@router.get("/timeline", response_model=list[TimelineItemOut])
def get_timeline(event_id: str, db: Session = Depends(get_db)) -> list[TimelineItemOut]:
    _require_event(db, event_id)
    return [
        TimelineItemOut.model_validate(event_repo._event_to_dict_timeline(i))
        for i in event_repo.list_timeline(db, event_id)
    ]


@router.post("/timeline", response_model=TimelineItemOut, status_code=status.HTTP_201_CREATED)
def add_timeline(
    event_id: str, payload: TimelineItemCreate, db: Session = Depends(get_db)
) -> TimelineItemOut:
    _require_event(db, event_id)
    item = event_repo.add_timeline_item(db, event_id, payload.model_dump())
    return TimelineItemOut.model_validate(event_repo._event_to_dict_timeline(item))


@router.patch("/timeline/{item_id}", response_model=TimelineItemOut)
def update_timeline(
    event_id: str,
    item_id: str,
    payload: TimelineItemUpdate,
    db: Session = Depends(get_db),
) -> TimelineItemOut:
    _require_event(db, event_id)
    item = event_repo.get_timeline_item(db, item_id)
    if item is None or item.event_id != event_id:
        raise HTTPException(status_code=404, detail="Timeline item not found.")
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    if "done" in changes:
        changes["done"] = 1 if changes["done"] else 0
    updated = event_repo.update_timeline_item(db, item, changes)
    return TimelineItemOut.model_validate(event_repo._event_to_dict_timeline(updated))


@router.delete("/timeline/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_timeline(
    event_id: str, item_id: str, db: Session = Depends(get_db)
) -> None:
    _require_event(db, event_id)
    item = event_repo.get_timeline_item(db, item_id)
    if item is None or item.event_id != event_id:
        raise HTTPException(status_code=404, detail="Timeline item not found.")
    event_repo.delete_timeline_item(db, item)


# --------------------------------------------------------------------------- #
# Expenses
# --------------------------------------------------------------------------- #
@router.get("/expenses", response_model=list[ExpenseOut])
def get_expenses(event_id: str, db: Session = Depends(get_db)) -> list[ExpenseOut]:
    _require_event(db, event_id)
    return [
        ExpenseOut.model_validate(event_repo._event_to_dict_expense(i))
        for i in event_repo.list_expenses(db, event_id)
    ]


@router.post("/expenses", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def add_expense(
    event_id: str, payload: ExpenseCreate, db: Session = Depends(get_db)
) -> ExpenseOut:
    _require_event(db, event_id)
    item = event_repo.add_expense(db, event_id, payload.model_dump())
    return ExpenseOut.model_validate(event_repo._event_to_dict_expense(item))


@router.patch("/expenses/{expense_id}", response_model=ExpenseOut)
def update_expense(
    event_id: str,
    expense_id: str,
    payload: ExpenseUpdate,
    db: Session = Depends(get_db),
) -> ExpenseOut:
    _require_event(db, event_id)
    item = event_repo.get_expense(db, expense_id)
    if item is None or item.event_id != event_id:
        raise HTTPException(status_code=404, detail="Expense not found.")
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    if "paid" in changes:
        changes["paid"] = 1 if changes["paid"] else 0
    updated = event_repo.update_expense(db, item, changes)
    return ExpenseOut.model_validate(event_repo._event_to_dict_expense(updated))


@router.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    event_id: str, expense_id: str, db: Session = Depends(get_db)
) -> None:
    _require_event(db, event_id)
    item = event_repo.get_expense(db, expense_id)
    if item is None or item.event_id != event_id:
        raise HTTPException(status_code=404, detail="Expense not found.")
    event_repo.delete_expense(db, item)



@router.delete("/checklist/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_checklist(
    event_id: str, item_id: str, db: Session = Depends(get_db)
) -> None:
    _require_event(db, event_id)
    item = event_repo.get_checklist_item(db, item_id)
    if item is None or item.event_id != event_id:
        raise HTTPException(status_code=404, detail="Checklist item not found.")
    event_repo.delete_checklist_item(db, item)
