"""Timeline templates for the deterministic planner.

Each entry is ``(phase, title, description, day_offset, owner)``. A negative
``day_offset`` means "this many days before the event"; ``0`` means the event
day itself.
"""
from __future__ import annotations

PREPARATION_TIMELINE: list[tuple[str, str, str, int, str]] = [
    ("preparation", "Define the plan and shortlist", "Fix the guest list size, budget ceiling and shortlist of themes and venues.", -90, "You"),
    ("preparation", "Book the venue", "Visit shortlisted venues, negotiate and pay the booking deposit.", -75, "You"),
    ("preparation", "Confirm the date, time and guest count", "Lock the date with the venue and agree a realistic headcount range.", -60, "You"),
    ("preparation", "Shortlist and compare vendors", "Collect quotes for catering, decor, photography and entertainment.", -55, "You"),
    ("preparation", "Book catering and finalise the menu", "Lock the caterer, agree the menu and note dietary requirements.", -45, "You"),
    ("preparation", "Send invitations", "Send digital invitations and track RSVPs against the headcount.", -40, "You"),
    ("preparation", "Confirm decor and florals", "Agree the theme, palette and floral elements with the decorator.", -30, "You"),
    ("preparation", "Book photography and entertainment", "Confirm the photo coverage, and book music or DJ.", -28, "You"),
    ("preparation", "Plan travel and stay for guests", "Share travel guidance and arrange room blocks where needed.", -21, "You"),
    ("preparation", "Finalise guest list and seating", "Lock the final headcount and plan seating arrangements.", -14, "You"),
    ("preparation", "Prepare the run sheet", "Write the minute-by-minute schedule, vendor contacts and emergency plan.", -7, "You"),
    ("preparation", "Confirm every vendor one week out", "Call each vendor to reconfirm timing, payments and requirements.", -7, "You"),
    ("preparation", "Pack emergency kit and welcome kits", "Stock first-aid basics, spare decor, and welcome hampers.", -2, "You"),
]

EVENT_DAY_TIMELINE: list[tuple[str, str, str, int, str]] = [
    ("event_day", "Vendor setup begins", "Decor, lighting and furniture setup begins at the venue.", 0, "Venue"),
    ("event_day", "Catering and kitchen setup", "Kitchen prep, buffet and live-counter setup.", 0, "Caterer"),
    ("event_day", "Photography setup and first shots", "Photographer arrives, captures detail and getting-ready shots.", 0, "Photographer"),
    ("event_day", "Guest arrival and welcome", "Welcome desk opens, welcome drinks served.", 0, "Operations"),
    ("event_day", "Main programme and speeches", "Run the ceremony, speeches and key performances to the run sheet.", 0, "You"),
    ("event_day", "Food service", "Buffet or plated service opens as per the catering plan.", 0, "Caterer"),
    ("event_day", "Entertainment and dancing", "Entertainment set and open floor for guests.", 0, "Entertainment"),
    ("event_day", "Dessert, cake and guest send-off", "Cake cutting, distribution of return gifts and guest departure.", 0, "You"),
    ("event_day", "Vendor settlement and cleanup", "Final payments, waste clearance and equipment collection.", 0, "Operations"),
]
