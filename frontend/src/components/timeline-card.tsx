"use client";

import { useMemo, useState } from "react";

import { useEventora } from "@/components/eventora-provider";
import {
  Button,
  Card,
  CardHeader,
  EmptyState,
  inputClass,
  selectClass,
} from "@/components/ui";
import { api } from "@/lib/api";
import { formatOffset } from "@/lib/format";

export function TimelineCard() {
  const { selectedEvent, selectedEventId, refreshSelected } = useEventora();
  const [busy, setBusy] = useState(false);
  const [title, setTitle] = useState("");
  const [phase, setPhase] = useState<"preparation" | "event_day">("preparation");
  const [offset, setOffset] = useState(-14);

  const items = selectedEvent?.timeline ?? [];

  const grouped = useMemo(() => {
    const map = new Map<string, typeof items>();
    items.forEach((item) => {
      const list = map.get(item.phase) ?? [];
      list.push(item);
      map.set(item.phase, list);
    });
    return Array.from(map.entries());
  }, [items]);

  const done = items.filter((item) => item.done).length;

  async function toggle(itemId: string, value: boolean) {
    if (!selectedEventId) return;
    setBusy(true);
    try {
      await api.updateTimelineItem(selectedEventId, itemId, { done: value });
      await refreshSelected();
    } finally {
      setBusy(false);
    }
  }

  async function addItem() {
    if (!selectedEventId || !title.trim()) return;
    setBusy(true);
    try {
      await api.addTimelineItem(selectedEventId, {
        phase,
        title: title.trim(),
        day_offset: offset,
      });
      setTitle("");
      await refreshSelected();
    } finally {
      setBusy(false);
    }
  }

  async function removeItem(itemId: string) {
    if (!selectedEventId) return;
    setBusy(true);
    try {
      await api.deleteTimelineItem(selectedEventId, itemId);
      await refreshSelected();
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardHeader
        title="Timeline"
        description={
          items.length > 0
            ? `${done} of ${items.length} complete`
            : "Generate a plan to populate the preparation timeline and event-day schedule."
        }
      />

      {items.length === 0 ? (
        <EmptyState
          title="No timeline yet"
          description="Generate a plan to get a preparation schedule and the event-day run sheet."
        />
      ) : (
        <div className="divide-y divide-[var(--border)]">
          {grouped.map(([group, groupItems]) => (
            <div key={group}>
              <p className="bg-[var(--surface-muted)] px-5 py-2 text-xs font-semibold uppercase tracking-wide text-ink-500">
                {group === "preparation" ? "Preparation" : "Event day"}
              </p>
              <ul className="divide-y divide-[var(--border)]">
                {groupItems.map((item) => (
                  <li
                    key={item.id}
                    className="flex flex-wrap items-center gap-3 px-5 py-2.5"
                  >
                    <input
                      type="checkbox"
                      checked={item.done}
                      disabled={busy}
                      onChange={(event) => void toggle(item.id, event.target.checked)}
                      className="h-4 w-4 shrink-0 accent-[var(--color-brand-500)]"
                      aria-label={`Mark ${item.title} as done`}
                    />
                    <span className="w-28 shrink-0 text-xs text-ink-500">
                      {formatOffset(item.day_offset)}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p
                        className={`text-sm ${
                          item.done ? "text-ink-400 line-through" : ""
                        }`}
                      >
                        {item.title}
                      </p>
                      {item.description ? (
                        <p className="text-xs text-ink-500">{item.description}</p>
                      ) : null}
                    </div>
                    <span className="text-xs text-ink-400">{item.owner}</span>
                    <button
                      onClick={() => void removeItem(item.id)}
                      className="text-xs text-ink-400 hover:text-brand-600"
                      aria-label={`Remove ${item.title}`}
                    >
                      Remove
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}

      <div className="flex flex-wrap items-end gap-2 border-t border-[var(--border)] px-5 py-4">
        <div className="min-w-[14rem] flex-1">
          <label className="mb-1 block text-xs font-medium text-ink-600">Title</label>
          <input
            className={inputClass}
            value={title}
            placeholder="Add a milestone..."
            onChange={(event) => setTitle(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                void addItem();
              }
            }}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-ink-600">Phase</label>
          <select
            className={`${selectClass} w-32`}
            value={phase}
            onChange={(event) =>
              setPhase(event.target.value as "preparation" | "event_day")
            }
          >
            <option value="preparation">Preparation</option>
            <option value="event_day">Event day</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-ink-600">
            Days offset
          </label>
          <input
            type="number"
            className={`${inputClass} w-28`}
            value={offset}
            onChange={(event) => setOffset(Number(event.target.value) || 0)}
          />
        </div>
        <Button variant="secondary" onClick={() => void addItem()} disabled={busy}>
          Add milestone
        </Button>
      </div>
    </Card>
  );
}
