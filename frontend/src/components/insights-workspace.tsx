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
} from "@/components/ui";
import { api, type MLMetrics, type RecommendationResult } from "@/lib/api";
import { formatINR, titleCase } from "@/lib/format";

export function InsightsWorkspace() {
  const { selectedEvent, selectedEventId } = useEventora();
  const [result, setResult] = useState<RecommendationResult | null>(null);
  const [metrics, setMetrics] = useState<MLMetrics | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!selectedEvent) return;
    setBusy(true);
    setError(null);
    try {
      const [recommendations, modelMetrics] = await Promise.all([
        api.recommend({
          event_type: selectedEvent.event_type,
          budget: selectedEvent.budget,
          guest_count: selectedEvent.guest_count,
          preferences: selectedEvent.preferences,
          style: selectedEvent.style,
          top_k: 9,
        }),
        api.mlMetrics().catch(() => null),
      ]);
      setResult(recommendations);
      setMetrics(modelMetrics);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not load recommendations.",
      );
    } finally {
      setBusy(false);
    }
  }, [selectedEvent]);

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedEventId, selectedEvent?.preferences, selectedEvent?.budget]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Insights</h1>
          <p className="text-sm text-ink-500">
            Content-based recommendations and the honest numbers behind them.
          </p>
        </div>
        <EventSelector />
      </div>

      {!selectedEvent ? (
        <Card>
          <EmptyState
            title="No event selected"
            description="Choose an event to get recommendations matched to its type, style, budget and preferences."
          />
        </Card>
      ) : (
        <>
          <Card>
            <CardHeader
              title="Recommended for this event"
              description="k-nearest-neighbours over a curated catalogue (Model B)."
              action={
                <Button onClick={() => void load()} disabled={busy} size="sm">
                  {busy ? "Loading..." : "Refresh"}
                </Button>
              }
            />
            <div className="space-y-4 px-5 py-5">
              {error ? (
                <ErrorBanner message={error} onRetry={() => void load()} />
              ) : !result ? (
                <Spinner label="Finding matches" />
              ) : (
                <>
                  <p className="text-sm text-ink-600">{result.explanation}</p>
                  <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                    {result.recommendations.map((item) => (
                      <div
                        key={item.rank}
                        className="rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] p-4"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <p className="text-sm font-semibold">{item.name}</p>
                          <span className="shrink-0 rounded-full bg-brand-500/15 px-2 py-0.5 text-[11px] font-semibold text-brand-600">
                            {(item.score * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div className="mt-1.5 flex flex-wrap gap-1.5">
                          <Badge className="border-[var(--border)] bg-[var(--surface)] text-ink-500">
                            {titleCase(item.category)}
                          </Badge>
                          {item.price_band ? (
                            <Badge className="border-[var(--border)] bg-[var(--surface)] text-ink-500">
                              {titleCase(item.price_band)}
                            </Badge>
                          ) : null}
                        </div>
                        {item.description ? (
                          <p className="mt-2 text-xs text-ink-600">
                            {item.description}
                          </p>
                        ) : null}
                        <p className="mt-2 text-xs text-ink-500">{item.reason}</p>
                        {item.estimated_cost_per_guest ? (
                          <p className="mt-2 text-xs font-medium text-ink-700">
                            ~{formatINR(item.estimated_cost_per_guest)} per guest
                          </p>
                        ) : null}
                        {item.tags.length > 0 ? (
                          <div className="mt-2 flex flex-wrap gap-1">
                            {item.tags.slice(0, 4).map((tag) => (
                              <span
                                key={tag}
                                className="rounded-full bg-[var(--surface)] px-2 py-0.5 text-[10px] text-ink-500"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        ) : null}
                      </div>
                    ))}
                  </div>
                  <Caveat>{result.method_note}</Caveat>
                </>
              )}
            </div>
          </Card>

          <ModelMetricsCard metrics={metrics} />
        </>
      )}
    </div>
  );
}

function ModelMetricsCard({ metrics }: { metrics: MLMetrics | null }) {
  if (!metrics) {
    return (
      <Card>
        <CardHeader title="Model metrics" />
        <Spinner label="Loading metrics" />
      </Card>
    );
  }

  const cost = metrics.cost_model as Record<string, number | string>;
  const rec = metrics.recommendation_model as Record<string, number | string>;
  const risk = metrics.risk_model as Record<string, unknown>;

  return (
    <Card>
      <CardHeader
        title="Model metrics"
        description="Reported evaluation results for the three models."
      />
      <div className="space-y-5 px-5 py-5">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Metric
            label="Cost model R2"
            value={Number(cost.r2 ?? 0).toFixed(4)}
            hint={String(cost.model ?? "")}
          />
          <Metric
            label="Cost model MAE"
            value={formatINR(Number(cost.mae ?? 0))}
            hint={`${Number(cost.n_samples ?? 0).toString()} synthetic rows`}
          />
          <Metric
            label="Risk accuracy"
            value={Number(risk.accuracy ?? 0).toFixed(4)}
            hint={String(risk.model ?? "")}
          />
          <Metric
            label="Catalogue size"
            value={String(rec.n_items ?? 0)}
            hint={String(rec.model ?? "")}
          />
        </div>

        <Caveat>{metrics.dataset_note}</Caveat>

        {typeof risk.accuracy_note === "string" ? (
          <p className="text-xs leading-relaxed text-ink-600">
            {risk.accuracy_note}
          </p>
        ) : null}
        {typeof rec.evaluation_note === "string" ? (
          <p className="text-xs leading-relaxed text-ink-600">
            {rec.evaluation_note}
          </p>
        ) : null}

        <p className="text-xs text-ink-400">
          Trained {metrics.generated_at ? new Date(metrics.generated_at).toUTCString() : "-"}
        </p>
      </div>
    </Card>
  );
}

function Metric({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] px-4 py-3">
      <p className="text-xs uppercase tracking-wide text-ink-500">{label}</p>
      <p className="mt-1 text-lg font-semibold">{value}</p>
      {hint ? <p className="mt-0.5 text-xs text-ink-400">{hint}</p> : null}
    </div>
  );
}
