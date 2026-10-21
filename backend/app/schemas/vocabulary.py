"""Controlled vocabularies shared by schemas, the ML pipelines and the AI layer.

Keeping these in one module means the synthetic dataset generator, the feature
encoders and the Pydantic validators can never drift apart.
"""
from __future__ import annotations

# --- Event categories -------------------------------------------------------
EVENT_TYPES = ["wedding", "birthday", "anniversary", "corporate", "college", "community"]
EVENT_TYPE_LABELS = {
    "wedding": "Wedding",
    "birthday": "Birthday",
    "anniversary": "Anniversary",
    "corporate": "Corporate Event",
    "college": "College Event",
    "community": "Community Celebration",
}

# --- Location tiers (city category) -----------------------------------------
CITY_TIERS = ["tier1_metro", "tier2_city", "tier3_town"]
CITY_TIER_LABELS = {
    "tier1_metro": "Tier-1 Metro",
    "tier2_city": "Tier-2 City",
    "tier3_town": "Tier-3 Town",
}

# --- Venue categories -------------------------------------------------------
VENUE_TYPES = ["banquet_hall", "hotel", "outdoor_garden", "farmhouse", "banquet_resort", "home"]
VENUE_TYPE_LABELS = {
    "banquet_hall": "Banquet Hall",
    "hotel": "Hotel Ballroom",
    "outdoor_garden": "Outdoor Garden",
    "farmhouse": "Farmhouse / Lawn",
    "banquet_resort": "Resort",
    "home": "Private Home",
}

# --- Duration buckets (hours) ----------------------------------------------
DURATION_HOURS = [3, 4, 5, 6, 8]

# --- Service tiers ----------------------------------------------------------
SERVICE_LEVELS = ["basic", "standard", "premium"]
SERVICE_LEVEL_LABELS = {
    "basic": "Basic",
    "standard": "Standard",
    "premium": "Premium",
}
CATERING_LEVELS = SERVICE_LEVELS
DECORATION_LEVELS = SERVICE_LEVELS
PHOTOGRAPHY_LEVELS = SERVICE_LEVELS

# --- Style / theme ----------------------------------------------------------
STYLES = ["Classic", "Modern", "Traditional", "Minimal", "Festive", "Luxury"]
THEMES = [
    "Elegant",
    "Garden Party",
    "Royal Heritage",
    "Modern Minimal",
    "Bollywood Glam",
    "Rustic Countryside",
    "Coastal Serenity",
    "Corporate Innovation",
    "Retro Disco",
    "Floral Romance",
]

# --- Budget risk labels -----------------------------------------------------
RISK_LOW = "low"
RISK_MEDIUM = "medium"
RISK_HIGH = "high"
RISK_LABELS = {RISK_LOW: "Low risk", RISK_MEDIUM: "Medium risk", RISK_HIGH: "High risk"}

# --- Currency ---------------------------------------------------------------
CURRENCY = "INR"


def _assert_unique(name: str, values: list[str]) -> None:
    if len(set(values)) != len(values):
        raise RuntimeError(f"{name} contains duplicate entries")


for _name, _values in [
    ("EVENT_TYPES", EVENT_TYPES),
    ("CITY_TIERS", CITY_TIERS),
    ("VENUE_TYPES", VENUE_TYPES),
    ("SERVICE_LEVELS", SERVICE_LEVELS),
    ("STYLES", STYLES),
    ("THEMES", THEMES),
]:
    _assert_unique(_name, _values)
