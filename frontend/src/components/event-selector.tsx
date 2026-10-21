"use client";

import { useEventora } from "@/components/eventora-provider";
import { daysUntil, formatDate, titleCase } from "@/lib/format";

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
    <div className="flex flex-wrap gap-2">
      {events.map((event) => {
        const active = event.id === selectedEventId;
        const days = daysUntil(event.event_date);
        return (
          <button
            key={event.id}
            onClick={() => selectEvent(event.id)}
            className={`rounded-xl border px-3 py-2 text-left transition-colors ${
              active
                ? "border-brand-400 bg-brand-500/10"
                : "border-[var(--border)] bg-[var(--surface)] hover:border-brand-300"
            }`}
          >
            <span className="block text-sm font-medium">{event.name}</span>
            <span className="block text-xs text-ink-500">
              {titleCase(event.event_type)} | {formatDate(event.event_date)}
              {days >= 0 ? ` | ${days} days away` : ""}
            </span>
          </button>
        );
      })}
    </div>
  );
}
