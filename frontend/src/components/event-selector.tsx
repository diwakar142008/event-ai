"use client";

import { useEventora } from "@/components/eventora-provider";
import { formatDate, titleCase } from "@/lib/format";
import { selectClass } from "@/components/ui";

export function EventSelector() {
  const { events, selectedEventId, selectEvent } = useEventora();

  if (events.length === 0) {
    return (
      <p className="text-xs text-ink-500">
        No events yet - create one on the Overview tab to unlock planning.
      </p>
    );
  }

  return (
    <label className="block min-w-0">
      <span className="sr-only">Selected event</span>
      <select className={`${selectClass} min-w-[13rem] max-w-full`} value={selectedEventId ?? ""} onChange={(event) => selectEvent(event.target.value || null)}>
        {events.map((event) => <option key={event.id} value={event.id}>{event.name} · {titleCase(event.event_type)} · {formatDate(event.event_date)} · {event.guest_count} guests</option>)}
      </select>
    </label>
  );
}
