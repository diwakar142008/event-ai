"use client";

import { useCallback, useEffect, useState } from "react";

import { useEventora } from "@/components/eventora-provider";
import { EventSelector } from "@/components/event-selector";
import {
  Badge,
  Button,
  Card,
  CardHeader,
  Caveat,
  EmptyState,
  ErrorBanner,
  Spinner,
  inputClass,
} from "@/components/ui";
import { api, type BudgetRisk, type CostPrediction } from "@/lib/api";
import { formatINR, formatNumber, riskTone } from "@/lib/format";

export function BudgetWorkspace() {
  const { selectedEvent, selectedEventId, updateEvent, loading } = useEventora();
  const [cost, setCost] = useState<CostPrediction | null>(null);
  const [risk, setRisk] = useState<BudgetRisk | null>(null);
  const [contingency, setContingency] = useState(10);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyse = useCallback(async () => {
    if (!selectedEvent) return;
    setBusy(true);
    setError(null);
    try {
      const prediction = await api.predictCost({
        event_type: selectedEvent.event_type,
        guest_count: selectedEvent.guest_count,
        city: selectedEvent.city,
        venue_type: selectedEvent.venue_type,
        duration_hours: selectedEvent.duration_hours,
        catering_level: selectedEvent.catering_level,
        decoration_level: selectedEvent.decoration_level,
        photography: selectedEvent.photography,
        budget: selectedEvent.budget,
      });
      setCost(prediction);

      const riskResult = await api.budgetRisk({
        budget: selectedEvent.budget,
        predicted_cost: prediction.predicted_cost,
        contingency_pct: contingency,
        guest_count: selectedEvent.guest_count,
      });
      setRisk(riskResult);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not run the cost analysis.",
      );
    } finally {
      setBusy(false);
    }
  }, [selectedEvent, contingency]);

  useEffect(() => {
    void analyse();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedEventId, selectedEvent?.budget, selectedEvent?.guest_count]);

  if (loading) return <Spinner label="Loading budget" />;

  const topFeatures = cost
    ? Object.entries(cost.feature_importances).slice(0, 6)
    : [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Budget</h1>
          <p className="text-sm text-ink-500">
            Cost estimate, variance against budget and risk of going over.
          </p>
        </div>
        <EventSelector />
      </div>

      {!selectedEvent ? (
        <Card>
          <EmptyState
            title="No event selected"
            description="Choose an event to see its ML cost estimate and budget-risk assessment."
          />
        </Card>
      ) : (
        <>
          <Card>
            <CardHeader
              title="Estimate"
              description="Random Forest cost model (Model A) trained on a synthetic dataset."
              action={
                <Button onClick={() => void analyse()} disabled={busy} size="sm">
                  {busy ? "Running..." : "Re-run"}
                </Button>
              }
            />
            <div className="px-5 py-5">
              {error ? (
                <ErrorBanner message={error} onRetry={() => void analyse()} />
              ) : cost ? (
                <div className="space-y-5">
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <Metric
                      label="Estimated cost"
                      value={formatINR(cost.predicted_cost)}
                      hint={`${formatINR(cost.per_guest_cost)} per guest`}
                    />
                    <Metric
                      label="Planning range"
                      value={`${formatINR(cost.lower_bound)} - ${formatINR(cost.upper_bound)}`}
                      hint="Model error band (1x training RMSE)"
                    />
                    <Metric
                      label="Your budget"
                      value={formatINR(cost.budget ?? 0)}
                      hint={
                        cost.budget_gap !== null
                          ? cost.budget_gap >= 0
                            ? `${formatINR(cost.budget_gap)} headroom`
                            : `${formatINR(Math.abs(cost.budget_gap))} over`
                          : undefined
                      }
                    />
                    <Metric
                      label="Budget usage"
                      value={
                        cost.budget_usage_pct !== null
                          ? `${cost.budget_usage_pct.toFixed(0)}%`
                          : "-"
                      }
                      hint={
                        cost.budget_status === "within_budget"
                          ? "Within budget"
                          : cost.budget_status === "over_budget"
                            ? "Over budget"
                            : undefined
                      }
                      tone={
                        cost.budget_status === "over_budget"
                          ? "bad"
                          : cost.budget_status === "within_budget"
                            ? "good"
                            : "neutral"
                      }
                    />
                  </div>

                  <Caveat>{cost.data_note}</Caveat>
                  <p className="text-xs text-ink-500">{cost.confidence_note}</p>

                  {topFeatures.length > 0 ? (
                    <div>
                      <p className="mb-2 text-xs uppercase tracking-wide text-ink-500">
                        What drives the estimate
                      </p>
                      <div className="space-y-1.5">
                        {topFeatures.map(([feature, importance]) => (
                          <div key={feature} className="flex items-center gap-3">
                            <span className="w-44 shrink-0 truncate text-xs text-ink-600">
                              {feature.replace(/_/g, " ")}
                            </span>
                            <span className="h-2 flex-1 overflow-hidden rounded-full bg-ink-100">
                              <span
                                className="block h-full rounded-full bg-brand-500"
                                style={{
                                  width: `${Math.max(2, importance * 100)}%`,
                                }}
                              />
                            </span>
                            <span className="w-12 shrink-0 text-right text-xs text-ink-500">
                              {(importance * 100).toFixed(1)}%
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : null}
                </div>
              ) : (
                <Spinner label="Estimating cost" />
              )}
            </div>
          </Card>

          <Card>
            <CardHeader
              title="Budget risk"
              description="Decision Tree classifier (Model C) labels the risk of going over budget."
            />
            <div className="space-y-5 px-5 py-5">
              <div className="flex flex-wrap items-end gap-3">
                <div>
                  <label className="mb-1 block text-xs font-medium text-ink-600">
                    Contingency allowance
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    className={`${inputClass} w-28`}
                    value={contingency}
                    onChange={(event) => {
                      setContingency(Number(event.target.value) || 0);
                    }}
                  />
                </div>
                <span className="pb-2 text-xs text-ink-500">% of the estimate</span>
                <Button variant="secondary" onClick={() => void analyse()} disabled={busy}>
                  Update risk
                </Button>
              </div>

              {risk ? (
                <div className="space-y-4">
                  <div className="flex flex-wrap items-center gap-3">
                    <Badge className={riskTone(risk.risk_level)}>
                      {risk.risk_label}
                    </Badge>
                    <span className="text-xs text-ink-500">
                      Model confidence {(risk.confidence * 100).toFixed(0)}%
                    </span>
                    <span className="text-xs text-ink-500">
                      Recommended contingency {risk.recommended_contingency_pct}% (
                      {formatINR(risk.suggested_contingency)})
                    </span>
                  </div>

                  <div>
                    <p className="mb-1.5 text-xs uppercase tracking-wide text-ink-500">
                      Why
                    </p>
                    <ul className="space-y-1.5">
                      {risk.reasons.map((reason) => (
                        <li key={reason} className="text-sm">
                          {reason}
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <p className="mb-1.5 text-xs uppercase tracking-wide text-ink-500">
                      Ways to bring it down
                    </p>
                    <ul className="space-y-1.5">
                      {risk.saving_tips.map((tip) => (
                        <li key={tip} className="flex gap-2 text-sm">
                          <span className="text-brand-500">&#9679;</span>
                          <span>{tip}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <details className="rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-2">
                    <summary className="cursor-pointer text-sm font-medium">
                      Assumptions and method
                    </summary>
                    <ul className="mt-2 space-y-1.5">
                      {risk.assumptions.map((assumption) => (
                        <li
                          key={assumption}
                          className="text-xs leading-relaxed text-ink-600"
                        >
                          &bull; {assumption}
                        </li>
                      ))}
                    </ul>
                    <p className="mt-2 text-xs leading-relaxed text-ink-500">
                      {risk.method_note}
                    </p>
                  </details>
                </div>
              ) : (
                <Spinner label="Assessing risk" />
              )}
            </div>
          </Card>

          <Card>
            <CardHeader
              title="Adjust the plan"
              description="Change the budget or guest count and re-run the estimate."
            />
            <div className="grid gap-4 px-5 py-5 sm:grid-cols-2">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-ink-800">
                  Budget (INR)
                </label>
                <input
                  type="number"
                  min={0}
                  step={10000}
                  className={inputClass}
                  defaultValue={selectedEvent.budget}
                  onBlur={(event) => {
                    const value = Number(event.target.value);
                    if (value !== selectedEvent.budget && value >= 0) {
                      void updateEvent(selectedEvent.id, { budget: value });
                    }
                  }}
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-ink-800">
                  Guest count
                </label>
                <input
                  type="number"
                  min={1}
                  max={2000}
                  className={inputClass}
                  defaultValue={selectedEvent.guest_count}
                  onBlur={(event) => {
                    const value = Number(event.target.value);
                    if (value !== selectedEvent.guest_count && value >= 1) {
                      void updateEvent(selectedEvent.id, { guest_count: value });
                    }
                  }}
                />
              </div>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}

function Metric({
  label,
  value,
  hint,
  tone = "neutral",
}: {
  label: string;
  value: string;
  hint?: string;
  tone?: "good" | "bad" | "neutral";
}) {
  const toneClass =
    tone === "good"
      ? "text-sage-500"
      : tone === "bad"
        ? "text-brand-600"
        : "text-ink-900";
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] px-4 py-3">
      <p className="text-xs uppercase tracking-wide text-ink-500">{label}</p>
      <p className={`mt-1 text-lg font-semibold ${toneClass}`}>{value}</p>
      {hint ? <p className="mt-0.5 text-xs text-ink-400">{hint}</p> : null}
    </div>
  );
}
