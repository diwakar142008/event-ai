"""AI plan-generation and chat routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories import event_repo
from app.schemas.event import ChatOut, ChatRequest, GeneratePlanOut, GeneratePlanRequest
from app.services.ai_service import chat as run_chat
from app.services.ai_service import generate_plan

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/plan", response_model=GeneratePlanOut)
def create_plan(
    payload: GeneratePlanRequest, db: Session = Depends(get_db)
) -> GeneratePlanOut:
    """Generate a structured plan for an event (AI, or deterministic fallback)."""
    if payload.event_id:
        event = event_repo.get_event(db, payload.event_id)
        if event is None:
            raise HTTPException(
                status_code=404, detail=f"Event '{payload.event_id}' not found."
            )
        event_data = event_repo._event_to_dict(event)
    elif payload.event is not None:
        event_data = payload.event.model_dump()
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either an 'event_id' or an inline 'event' payload.",
        )

    result = generate_plan(event_data, payload.extra_instructions)

    # Persist the plan and, on first generation, seed the working checklist,
    # timeline and budget lines from the plan so the workspace is usable.
    if payload.event_id:
        event_repo.save_plan(db, payload.event_id, result["plan"], result["source"])
        plan = result["plan"]
        if payload.regenerate or not event_repo.list_checklist(db, payload.event_id):
            event_repo.replace_event_workspace(
                db,
                payload.event_id,
                checklist=plan.get("checklist", []),
                timeline=plan.get("timeline", []),
                expenses=[
                    {
                        "category": line.get("category", "General"),
                        "description": line.get("description", ""),
                        "estimated": line.get("estimated_cost", 0),
                    }
                    for line in plan.get("budget_breakdown", [])
                ],
            )

    return GeneratePlanOut.model_validate(result)


@router.post("/chat", response_model=ChatOut)
def chat(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatOut:
    """Ask the planner a question about an event."""
    event_data = None
    if payload.event_id:
        event = event_repo.get_event(db, payload.event_id)
        if event is None:
            raise HTTPException(
                status_code=404, detail=f"Event '{payload.event_id}' not found."
            )
        event_data = event_repo._event_to_dict(event)

    result = run_chat(payload.message, event_data, payload.history)
    return ChatOut.model_validate(result)
