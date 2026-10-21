"""Deterministic event planner — template helpers.

The planner is the **fallback** used whenever no LLM provider is configured or
the provider call fails. It is fully deterministic: the same event always
produces the same plan, with no network calls and no API key required.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from app.ml.catalogue_index import RECOMMENDATION_ITEMS

# --- theme colour palettes --------------------------------------------------
PALETTES: dict[str, list[str]] = {
    "Elegant": ["#F5EFE6", "#C9A227", "#8C7853", "#2F2A26"],
    "Garden Party": ["#EAF4E4", "#A8C686", "#D98E73", "#4F6F52"],
    "Royal Heritage": ["#8C1D40", "#E0A458", "#F4E1C1", "#2B1B17"],
    "Modern Minimal": ["#F4F4F5", "#111827", "#6B7280", "#E5E7EB"],
    "Bollywood Glam": ["#E0218A", "#F7B32B", "#2D3047", "#00B4D8"],
    "Rustic Countryside": ["#8B5E3C", "#D7B98E", "#5C7A4B", "#F1E7D3"],
    "Coastal Serenity": ["#DCE9F2", "#7FA8C9", "#F7F4EC", "#2E5266"],
    "Corporate Innovation": ["#123B5E", "#2E7DB8", "#F0A202", "#F5F7FA"],
    "Retro Disco": ["#FF4E98", "#FFD166", "#4B2E83", "#08D9D6"],
    "Floral Romance": ["#F6D5D5", "#C97C5D", "#7A9E7E", "#FFF3E6"],
}

# --- checklist templates ----------------------------------------------------
BASE_CHECKLIST: list[tuple[str, str, str]] = [
    ("Venue", "Shortlist and visit venues", "Venue"),
    ("Venue", "Confirm venue date and deposit", "Venue"),
    ("Catering", "Get 3 catering quotes for the final headcount", "Caterer"),
    ("Catering", "Finalise menu and dietary requirements", "Caterer"),
    ("Catering", "Confirm cake and dessert table", "Bakery"),
    ("Decor", "Agree decor theme and colour palette", "Decorator"),
    ("Decor", "Book florals and stage backdrop", "Florist"),
    ("Decor", "Confirm lighting and sound rental", "Decorator"),
    ("Photography", "Book photographer and check coverage hours", "Photographer"),
    ("Photography", "Book videographer (if required)", "Videographer"),
    ("Attire", "Finalise outfits and confirm fitting", "Attire"),
    ("Invitations", "Send invitations or save-the-dates", "Stationery"),
    ("Invitations", "Track RSVPs and finalise headcount", "Stationery"),
    ("Guests", "Arrange guest travel and stay", "Travel"),
    ("Guests", "Plan welcome kit / hampers", "Gifting"),
    ("Entertainment", "Book music, DJ or live performance", "Entertainment"),
    ("Entertainment", "Plan games or activities for the programme", "Entertainment"),
    ("Logistics", "Prepare run sheet and vendor contact sheet", "Planner"),
    ("Logistics", "Arrange transport and parking", "Transport"),
    ("Logistics", "Hire tables, chairs, linen and crockery", "Rentals"),
    ("Safety", "Brief first-aid and emergency contacts", "Safety"),
    ("Hygiene", "Plan waste management and cleanup crew", "Operations"),
]

EVENT_DAY_CHECKLIST: list[tuple[str, str, str]] = [
    ("On the day", "Venue handover and decor check", "Venue"),
    ("On the day", "Final vendor arrival and setup check", "Operations"),
    ("On the day", "Catering final headcount confirmation", "Caterer"),
    ("On the day", "Guest welcome and welcome desk", "Operations"),
    ("On the day", "Photography start and key-shot list", "Photographer"),
    ("On the day", "Speech and programme run-through", "Planner"),
    ("On the day", "Cue music, lighting and entertainment", "Entertainment"),
    ("On the day", "Distribution of return gifts", "Gifting"),
    ("On the day", "Final guest count and vendor settlement", "Planner"),
]
