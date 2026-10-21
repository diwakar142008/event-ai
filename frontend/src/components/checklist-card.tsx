"use client";

import { useMemo, useState } from "react";

import { useEventora } from "@/components/eventora-provider";
import {
  Badge,
  Button,
  Card,
  CardHeader,
  EmptyState,
  inputClass,
  selectClass,
} from "@/components/ui";
import { api } from "@/lib/api";
import { CHECKLIST_STATUSES, formatINR } from "@/lib/format";

export function ChecklistCard() {
  const { selectedEvent, selectedEventId, refreshSelected } = useEventora();
  const [filter, setFilter] = useState<string>("all");
  const [newItem, setNewItem] = useState("");
  const [busy, setBusy] = useState(false);
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);

  const items = useMemo(() => selectedEvent?.checklist ?? [], [selectedEvent?.checklist]);

  const grouped = useMemo(() => {
    const visible = items.filter((item) =>
      (filter === "all" || item.status === filter) &&
      item.item.toLocaleLowerCase().includes(search.trim().toLocaleLowerCase()),
    );
    const map = new Map<string, typeof visible>();
    visible.forEach((item) => {
      const list = map.get(item.category) ?? [];
      list.push(item);
      map.set(item.category, list);
    });
    return Array.from(map.entries());
  }, [items, filter, search]);

  const completed = items.filter((item) => item.status === "completed").length;
  const totalCost = items.reduce((sum, item) => sum + (item.estimated_cost || 0), 0);

  async function setStatus(itemId: string, status: string) {
    if (!selectedEventId) return;
    setBusy(true);
    setError(null);
    try {
      await api.updateChecklistItem(selectedEventId, itemId, { status });
      await refreshSelected();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update this task.");
    } finally {
      setBusy(false);
    }
  }

  async function addItem() {
    if (!selectedEventId || !newItem.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await api.addChecklistItem(selectedEventId, {
        category: "Custom",
        item: newItem.trim(),
      });
      setNewItem("");
      await refreshSelected();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add this task.");
    } finally {
      setBusy(false);
    }
  }

  async function removeItem(itemId: string) {
    if (!selectedEventId) return;
    if (!window.confirm("Remove this task from the checklist?")) return;
    setBusy(true);
    setError(null);
    try {
      await api.deleteChecklistItem(selectedEventId, itemId);
      await refreshSelected();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not remove this task.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardHeader
        title="Checklist"
        description={
          items.length > 0
            ? `${completed} of ${items.length} done | ${formatINR(totalCost)} of estimated task costs`
            : "Generate a plan to populate the checklist, or add tasks yourself."
        }
        action={
          <div className="flex flex-wrap gap-2">
          <input aria-label="Search checklist" className={`${inputClass} w-44`} value={search} placeholder="Search tasks" onChange={(event) => setSearch(event.target.value)} />
          <select aria-label="Filter checklist by status"
            className={`${selectClass} w-40`}
            value={filter}
            onChange={(event) => setFilter(event.target.value)}
          >
            <option value="all">All</option>
            {CHECKLIST_STATUSES.map((status) => (
              <option key={status} value={status}>
                {status[0].toUpperCase() + status.slice(1)}
              </option>
            ))}
          </select>
          </div>
        }
      />
      {error ? <p role="alert" className="px-5 pt-4 text-sm text-brand-700">{error}</p> : null}
      <p className="sr-only" aria-live="polite">{busy ? "Saving checklist changes" : "Checklist changes saved"}</p>

      {items.length === 0 ? (
        <EmptyState
          title="No checklist items yet"
          description="Generate a plan to get a full task list, or add the first task below."
        />
      ) : (
        <div className="divide-y divide-[var(--border)]">
          {grouped.map(([category, categoryItems]) => (
            <div key={category}>
              <p className="bg-[var(--surface-muted)] px-5 py-2 text-xs font-semibold uppercase tracking-wide text-ink-500">
                {category}
              </p>
              <ul className="divide-y divide-[var(--border)]">
                {categoryItems.map((item) => (
                  <li
                    key={item.id}
                    className="flex flex-wrap items-center gap-3 px-5 py-2.5"
                  >
                    <select
                      className={`${selectClass} w-32 py-1.5 text-xs`}
                      value={item.status}
                      disabled={busy}
                      onChange={(event) => setStatus(item.id, event.target.value)}
                    >
                      {CHECKLIST_STATUSES.map((status) => (
                        <option key={status} value={status}>
                          {status[0].toUpperCase() + status.slice(1)}
                        </option>
                      ))}
                    </select>
                    <span className="min-w-0 flex-1 text-sm">
                      {item.item}
                    </span>
                    {item.vendor_type ? (
                      <Badge className="border-[var(--border)] bg-[var(--surface-muted)] text-ink-500">
                        {item.vendor_type}
                      </Badge>
                    ) : null}
                    {item.estimated_cost > 0 ? (
                      <span className="text-xs text-ink-500">
                        {formatINR(item.estimated_cost)}
                      </span>
                    ) : null}
                    <button
                      onClick={() => void removeItem(item.id)}
                      className="text-xs text-ink-400 hover:text-brand-600"
                      aria-label={`Remove ${item.item}`}
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

      <div className="flex flex-wrap gap-2 border-t border-[var(--border)] px-5 py-4">
        <input
          className={`${inputClass} max-w-sm`}
          value={newItem}
          placeholder="Add a task..."
          onChange={(event) => setNewItem(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              void addItem();
            }
          }}
        />
        <Button variant="secondary" onClick={() => void addItem()} disabled={busy}>
          Add task
        </Button>
      </div>
    </Card>
  );
}
