"""Deterministic event planner.

This module is the **fallback** used whenever no LLM provider is configured or
the provider call fails. It is fully deterministic: the same event always
produces the same plan, with no network calls and no API key required.

The planner combines:
  * the cost model's own breakdown logic (so the plan's numbers agree with
    the cost estimate shown elsewhere in the UI),
  * the recommendation catalogue (so suggestions come from the same
    curated source the recommender uses),
  * template checklists and timelines that scale with the event's guest count,
    duration and service tiers.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from app.ml.dataset import compute_total_cost
from app.ml.catalogue_index import RECOMMENDATION_ITEMS
from app.services.planner_templates import (
    BASE_CHECKLIST,
    EVENT_DAY_CHECKLIST,
    PALETTES,
)
from app.services.planner_timeline import (
    EVENT_DAY_TIMELINE,
    PREPARATION_TIMELINE,
)


def _scale_timeline(
    base: list[tuple[str, str, str, int, str]], event_date: date
) -> list[dict[str, Any]]:
    """Return timeline entries with concrete dates attached."""
    entries: list[dict[str, Any]] = []
    for phase, title, description, offset, owner in base:
        target = event_date + timedelta(days=offset)
        entries.append(
            {
                "phase": phase,
                "title": title,
                "description": description,
                "day_offset": offset,
                "owner": owner,
                "date": target.isoformat(),
            }
        )
    return entries


def _pick_catalogue(
    event_type: str, style: str, budget_per_guest: float, count: int
) -> list[Any]:
    """Select catalogue items relevant to the event, deterministically."""
    scored: list[tuple[float, Any]] = []
    for item in RECOMMENDATION_ITEMS:
        type_match = 1.0 if event_type in item.event_types else 0.0
        style_match = 1.0 if style in item.styles else 0.0
        # Prefer items whose per-guest cost is close to the planned budget.
        cost_gap = abs(item.cost_per_guest - budget_per_guest) / max(budget_per_guest, 1.0)
        cost_fit = max(0.0, 1.0 - min(cost_gap, 1.0))
        score = type_match * 2.0 + style_match * 1.0 + cost_fit * 0.8 + item.popularity * 0.5
        scored.append((score, item))
    scored.sort(key=lambda pair: (-pair[0], pair[1].name))
    return [item for _, item in scored[:count]]


def _schedule_for_duration(duration_hours: int) -> list[dict[str, Any]]:
    """Build an event-day schedule that fits the chosen duration."""
    start_hour = 17
    blocks: list[tuple[str, str, str]] = [
        ("Guest arrival & welcome drinks", "60", "Welcome desk, welcome drinks and light music."),
        ("Ceremony / formal opening", "75", "Main ritual, speeches or keynote segment."),
        ("Cocktail hour & photographs", "60", "Group photographs and informal guest interaction."),
        ("Food service", "75", "Buffet or plated service, served to the seating plan."),
        ("Entertainment & open dancing", "90", "Performances, live music and dancing."),
        ("Dessert, cake & send-off", "45", "Cake cutting, return gifts and guest departure."),
    ]
    # Scale the block durations to fit the requested event length.
    total_reference = 60 + 75 + 60 + 75 + 90 + 45
    factor = max(0.5, min(2.0, duration_hours / 5.0))

    schedule: list[dict[str, Any]] = []
    current = start_hour * 60
    for title, minutes, notes in blocks:
        length = max(20, int(int(minutes) * factor))
        start_min = current
        end_min = current + length
        current = end_min
        schedule.append(
            {
                "start_time": f"{start_min // 60:02d}:{start_min % 60:02d}",
                "end_time": f"{end_min // 60:02d}:{end_min % 60:02d}",
                "activity": title,
                "notes": notes,
            }
        )
    return schedule


def generate_deterministic_plan(event: dict[str, Any]) -> dict[str, Any]:
    """Build a complete, deterministic plan for an event.

    ``event`` is a dict matching the :class:`app.schemas.event.EventCreate`
    shape. The returned payload matches :class:`app.schemas.plan.EventPlanSchema`.
    """
    event_type = event["event_type"]
    style = event["style"]
    theme = event["theme"]
    guests = int(event["guest_count"])
    budget = float(event["budget"])
    duration = int(event["duration_hours"])
    event_date = event["event_date"]
    if isinstance(event_date, str):
        event_date = date.fromisoformat(event_date)

    breakdown = compute_total_cost(
        event_type=event_type,
        guest_count=guests,
        city=event["city"],
        venue_type=event["venue_type"],
        duration_hours=duration,
        catering_level=event["catering_level"],
        decoration_level=event["decoration_level"],
        photography=event["photography"],
    )
    per_guest = breakdown["total"] / guests if guests else 0.0

    # --- budget lines ------------------------------------------------------
    budget_lines = [
        {
            "category": "Venue",
            "description": f"{event['venue_type'].replace('_', ' ').title()} rental for {duration} hours",
            "estimated_cost": round(breakdown["venue"], 2),
            "priority": "must_have",
        },
        {
            "category": "Catering",
            "description": f"{event['catering_level'].title()} menu for {guests} guests",
            "estimated_cost": round(breakdown["catering"], 2),
            "priority": "must_have",
        },
        {
            "category": "Decoration",
            "description": f"{event['decoration_level'].title()} decor package and florals",
            "estimated_cost": round(breakdown["decoration"], 2),
            "priority": "should_have",
        },
        {
            "category": "Photography",
            "description": f"{event['photography'].title()} photography coverage",
            "estimated_cost": round(breakdown["photography"], 2),
            "priority": "should_have",
        },
        {
            "category": "Contingency",
            "description": "Buffer for last-minute additions and price movement",
            "estimated_cost": round(breakdown["extras"], 2),
            "priority": "should_have",
        },
    ]

    # --- checklist ---------------------------------------------------------
    checklist: list[dict[str, Any]] = []
    cost_by_category = {
        "Venue": breakdown["venue"],
        "Catering": breakdown["catering"],
        "Decor": breakdown["decoration"],
        "Photography": breakdown["photography"],
        "Logistics": breakdown["extras"],
    }
    action_prefixes = (
        "Shortlist",
        "Get 3 catering",
        "Agree decor",
        "Book photographer",
        "Book videographer",
    )
    for category, item, vendor_type in BASE_CHECKLIST:
        checklist.append(
            {
                "category": category,
                "item": item,
                "vendor_type": vendor_type,
                "notes": "",
                "estimated_cost": 0.0,
            }
        )
    # Attach indicative costs to the "confirm/shortlist" actions so the
    # checklist carries a usable budget signal rather than all zeros.
    for entry in checklist:
        if entry["category"] in cost_by_category and entry["item"].startswith(action_prefixes):
            entry["estimated_cost"] = round(cost_by_category[entry["category"]] * 0.05, 2)

    for category, item, vendor_type in EVENT_DAY_CHECKLIST:
        checklist.append(
            {
                "category": category,
                "item": item,
                "vendor_type": vendor_type,
                "notes": "",
                "estimated_cost": 0.0,
            }
        )

    # --- timeline ----------------------------------------------------------
    timeline = _scale_timeline(PREPARATION_TIMELINE, event_date)
    timeline += _scale_timeline(EVENT_DAY_TIMELINE, event_date)

    # --- schedule ----------------------------------------------------------
    schedule = _schedule_for_duration(duration)

    # --- suggestions -------------------------------------------------------
    picks = _pick_catalogue(event_type, style, per_guest, 4)
    highlights = [f"{item.name} â€” {item.description}" for item in picks]

    palette = PALETTES.get(theme, PALETTES["Modern Minimal"])

    days_out = (event_date - date.today()).days
    if days_out < 0:
        timing_note = (
            "The event date is in the past. The preparation timeline is shown relative to "
            "the event date for reference only."
        )
    elif days_out < 30:
        timing_note = (
            f"Your event is {days_out} days away. Prioritise the venue, catering and "
            "photography bookings first, and compress the remaining preparation steps."
        )
    else:
        timing_note = (
            f"You have {days_out} days of runway, which is enough to follow the full "
            "preparation timeline and compare at least three quotes per service."
        )

    budget_line = (
        f"That is {((breakdown['total'] / budget) * 100):.0f}% of your budget of "
        f"INR {budget:,.0f}."
        if budget > 0
        else "Set a budget in the app to see how this plan compares against it."
    )

    tips = [
        f"Your plan costs about INR {breakdown['total']:,.0f} in total, or roughly "
        f"INR {per_guest:,.0f} per guest.",
        budget_line,
        "Catering is usually the largest line â€” fix the headcount early to avoid paying for empty seats.",
        "Book the venue first; almost everything else depends on the date and the guest capacity.",
        "Collect at least three quotes per major service before committing.",
        "Keep the contingency line untouched so it can absorb last-minute costs.",
    ]

    assumptions = [
        "This plan was generated by the deterministic planner (no LLM provider configured "
        "or the provider call failed), so it follows fixed templates rather than a "
        "bespoke creative concept.",
        "Cost lines use the same documented cost rules as the cost estimator, applied to "
        "a synthetic cost model â€” confirm every number with vendor quotes.",
        f"Headcount is assumed to stay at {guests} guests; catering cost scales linearly with it.",
        f"Timings assume a standard {duration}-hour event window and are scaled to fit.",
    ]

    return {
        "overview": {
            "concept": (
                f"A {event_type} for {guests} guests in a "
                f"{event['city'].replace('_', ' ')} setting, built around the "
                f"{theme} theme in a {style.lower()} style."
            ),
            "theme": theme,
            "style": style,
            "color_palette": palette,
            "highlights": highlights,
        },
        "budget_breakdown": budget_lines,
        "checklist": checklist,
        "timeline": timeline,
        "event_day_schedule": schedule,
        "tips": tips,
        "contingency_note": (
            f"INR {breakdown['extras']:,.0f} (about 8% of the estimate) is held back for "
            "last-minute additions, overtime charges and price movement."
        ),
        "assumptions": assumptions,
        "_meta": {
            "timing_note": timing_note,
            "total_cost": round(breakdown["total"], 2),
            "per_guest_cost": round(per_guest, 2),
        },
    }
