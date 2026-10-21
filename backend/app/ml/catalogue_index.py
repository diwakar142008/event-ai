"""Aggregated recommendation catalogue.

Thin re-export layer: the item type lives in :mod:`app.ml.catalogue` and the
entries live in per-category modules to keep every file readable.
"""
from __future__ import annotations

from app.ml.catalogue import (
    CATEGORY_ORDER,
    EVENT_TYPES,
    PRICE_BANDS,
    STYLES,
    CatalogueItem,
)
from app.ml.catalogue_activities import ACTIVITIES
from app.ml.catalogue_catering import CATERING
from app.ml.catalogue_decorations import DECORATIONS
from app.ml.catalogue_services import SERVICES
from app.ml.catalogue_themes import THEMES

RECOMMENDATION_ITEMS: list[CatalogueItem] = (
    THEMES + DECORATIONS + CATERING + ACTIVITIES + SERVICES
)

__all__ = [
    "CatalogueItem",
    "CATEGORY_ORDER",
    "EVENT_TYPES",
    "PRICE_BANDS",
    "STYLES",
    "RECOMMENDATION_ITEMS",
    "THEMES",
    "DECORATIONS",
    "CATERING",
    "ACTIVITIES",
    "SERVICES",
]
