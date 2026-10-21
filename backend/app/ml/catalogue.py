"""Catalogue item type — kept separate from the data modules to avoid cycles."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CatalogueItem:
    name: str
    category: str  # theme | decoration | catering | activity | service
    event_types: tuple[str, ...]
    styles: tuple[str, ...]
    price_band: str  # budget | mid | premium
    cost_per_guest: float
    tags: tuple[str, ...]
    description: str
    popularity: float = 0.5
    keywords: tuple[str, ...] = field(default_factory=tuple)


CATEGORY_ORDER = ["theme", "decoration", "catering", "activity", "service"]
PRICE_BANDS = ["budget", "mid", "premium"]
STYLES = ["Classic", "Modern", "Traditional", "Minimal", "Festive", "Luxury"]
EVENT_TYPES = [
    "wedding",
    "birthday",
    "anniversary",
    "corporate",
    "college",
    "community",
]
