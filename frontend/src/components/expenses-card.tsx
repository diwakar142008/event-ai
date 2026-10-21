"use client";

import { useState } from "react";

import { useEventora } from "@/components/eventora-provider";
import {
  Button,
  Card,
  CardHeader,
  EmptyState,
  inputClass,
} from "@/components/ui";
import { api } from "@/lib/api";
import { formatINR } from "@/lib/format";

export function ExpensesCard() {
  const { selectedEvent, selectedEventId, refreshSelected } = useEventora();
  const [busy, setBusy] = useState(false);
  const [description, setDescription] = useState("");
  const [estimated, setEstimated] = useState(0);
  const [actual, setActual] = useState(0);

  const expenses = selectedEvent?.expenses ?? [];
  const estimatedTotal = expenses.reduce((sum, e) => sum + (e.estimated || 0), 0);
  const actualTotal = expenses.reduce(
    (sum, e) => sum + (e.actual ?? e.estimated ?? 0),
    0,
  );
  const budget = selectedEvent?.budget ?? 0;
  const usage = budget > 0 ? (actualTotal / budget) * 100 : 0;

  async function addExpense() {
    if (!selectedEventId || !description.trim()) return;
    setBusy(true);
    try {
      await api.addExpense(selectedEventId, {
        category: "General",
        description: description.trim(),
        estimated,
        actual: actual > 0 ? actual : null,
      });
      setDescription("");
      setEstimated(0);
      setActual(0);
      await refreshSelected();
    } finally {
      setBusy(false);
    }
  }

  async function togglePaid(expenseId: string, paid: boolean) {
    if (!selectedEventId) return;
    setBusy(true);
    try {
      await api.updateExpense(selectedEventId, expenseId, { paid });
      await refreshSelected();
    } finally {
      setBusy(false);
    }
  }

  async function setActualCost(expenseId: string, value: number | null) {
    if (!selectedEventId) return;
    setBusy(true);
    try {
      await api.updateExpense(selectedEventId, expenseId, { actual: value });
      await refreshSelected();
    } finally {
      setBusy(false);
    }
  }

  async function removeExpense(expenseId: string) {
    if (!selectedEventId) return;
    setBusy(true);
    try {
      await api.deleteExpense(selectedEventId, expenseId);
      await refreshSelected();
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardHeader
        title="Budget tracker"
        description={
          expenses.length > 0
            ? `${formatINR(actualTotal)} committed of ${formatINR(budget)} budget (${usage.toFixed(0)}%)`
            : "Generate a plan to see the budget breakdown, then track actual spend here."
        }
      />

      {expenses.length === 0 ? (
        <EmptyState
          title="No budget lines yet"
          description="Generate a plan to get a cost breakdown you can then track against real vendor quotes."
        />
      ) : (
        <div className="divide-y divide-[var(--border)]">
          {expenses.map((expense) => (
            <div
              key={expense.id}
              className="flex flex-wrap items-center gap-3 px-5 py-2.5"
            >
              <input
                type="checkbox"
                checked={expense.paid}
                disabled={busy}
                onChange={(event) => void togglePaid(expense.id, event.target.checked)}
                className="h-4 w-4 shrink-0 accent-[var(--color-brand-500)]"
                aria-label={`Mark ${expense.description} as paid`}
              />
              <div className="min-w-[10rem] flex-1">
                <p className="text-sm">{expense.description}</p>
                <p className="text-xs text-ink-500">{expense.category}</p>
              </div>
              <span className="w-28 text-right text-sm text-ink-600">
                {formatINR(expense.estimated)}
              </span>
              <input
                type="number"
                min={0}
                step={1000}
                placeholder="Actual"
                disabled={busy}
                defaultValue={expense.actual ?? ""}
                onBlur={(event) => {
                  const raw = event.target.value;
                  void setActualCost(
                    expense.id,
                    raw === "" ? null : Number(raw),
                  );
                }}
                className={`${inputClass} w-28 py-1.5 text-right text-xs`}
              />
              <button
                onClick={() => void removeExpense(expense.id)}
                className="text-xs text-ink-400 hover:text-brand-600"
                aria-label={`Remove ${expense.description}`}
              >
                Remove
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="flex flex-wrap items-end gap-2 border-t border-[var(--border)] px-5 py-4">
        <div className="min-w-[12rem] flex-1">
          <label className="mb-1 block text-xs font-medium text-ink-600">
            Description
          </label>
          <input
            className={inputClass}
            value={description}
            placeholder="e.g. Venue deposit"
            onChange={(event) => setDescription(event.target.value)}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-ink-600">
            Estimated
          </label>
          <input
            type="number"
            min={0}
            step={1000}
            className={`${inputClass} w-32`}
            value={estimated}
            onChange={(event) => setEstimated(Number(event.target.value) || 0)}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-ink-600">Actual</label>
          <input
            type="number"
            min={0}
            step={1000}
            className={`${inputClass} w-32`}
            value={actual}
            onChange={(event) => setActual(Number(event.target.value) || 0)}
          />
        </div>
        <Button variant="secondary" onClick={() => void addExpense()} disabled={busy}>
          Add expense
        </Button>
      </div>
    </Card>
  );
}
