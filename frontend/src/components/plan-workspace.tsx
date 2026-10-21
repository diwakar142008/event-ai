"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { useEventora } from "@/components/eventora-provider";
import { EventSelector } from "@/components/event-selector";
import { PlanOverviewCard } from "@/components/plan-overview-card";
import { ChecklistCard } from "@/components/checklist-card";
import { TimelineCard } from "@/components/timeline-card";
import { ExpensesCard } from "@/components/expenses-card";
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
  selectClass,
} from "@/components/ui";
import { api } from "@/lib/api";
import {
  CHECKLIST_STATUSES,
  formatINR,
  formatOffset,
  statusTone,
  titleCase,
} from "@/lib/format";

export function PlanWorkspace() {
  const { selectedEvent, selectedEventId, refreshSelected, loading } = useEventora();
  const [generating, setGenerating] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [source, setSource] = useState<"ai" | "fallback" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [instructions, setInstructions] = useState("");

  const generate = useCallback(
    async (regenerate: boolean) => {
      if (!selectedEventId) return;
      setGenerating(true);
      setError(null);
      try {
        const result = await api.generatePlan({
          event_id: selectedEventId,
          extra_instructions: instructions,
          regenerate,
        });
        setSource(result.source);
        setNotice(result.notice);
        await refreshSelected();
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Could not generate a plan.",
        );
      } finally {
        setGenerating(false);
      }
    },
    [selectedEventId, instructions, refreshSelected],
  );

  // Generate a plan automatically the first time an event is opened here.
  useEffect(() => {
    if (
      selectedEventId &&
      selectedEvent &&
      !selectedEvent.plan &&
      !generating &&
      !error
    ) {
      void generate(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedEventId, selectedEvent?.plan]);

  if (loading) return <Spinner label="Loading the plan" />;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Plan</h1>
          <p className="text-sm text-ink-500">
            Checklist, timeline and day-of schedule for your event.
          </p>
        </div>
        <EventSelector />
      </div>

      {!selectedEvent ? (
        <Card>
          <EmptyState
            title="No event selected"
            description="Create or choose an event to generate a full plan - checklist, timeline, budget lines and a day-of schedule."
          />
        </Card>
      ) : (
        <>
          <Card>
            <CardHeader
              title="Generate the plan"
              description="The planner fills in the checklist, timeline and budget breakdown below. It works with or without an LLM API key."
            />
            <div className="space-y-4 px-5 py-5">
              <div className="flex flex-wrap items-center gap-2">
                <Button onClick={() => void generate(true)} disabled={generating}>
                  {generating ? "Generating..." : "Regenerate plan"}
                </Button>
                {source ? (
                  <Badge
                    className={
                      source === "ai"
                        ? "border-sage-500/30 bg-sage-500/15 text-sage-500"
                        : "border-gold-500/30 bg-gold-500/15 text-gold-600"
                    }
                  >
                    {source === "ai" ? "AI generated" : "Deterministic fallback"}
                  </Badge>
                ) : null}
              </div>

              <div>
                <label className="mb-1.5 block text-sm font-medium text-ink-800">
                  Extra instructions (optional)
                </label>
                <input
                  className={inputClass}
                  value={instructions}
                  onChange={(event) => setInstructions(event.target.value)}
                  placeholder="e.g. keep the ceremony outdoors and add a sangeet night"
                />
              </div>

              {notice ? <Caveat>{notice}</Caveat> : null}
              {error ? <ErrorBanner message={error} onRetry={() => void generate(true)} /> : null}
            </div>
          </Card>

          {selectedEvent.plan ? (
            <PlanOverviewCard
              concept={selectedEvent.plan.overview.concept}
              highlights={selectedEvent.plan.overview.highlights}
              palette={selectedEvent.plan.overview.color_palette}
              tips={selectedEvent.plan.tips}
              assumptions={selectedEvent.plan.assumptions}
              contingency={selectedEvent.plan.contingency_note}
              timingNote={selectedEvent.plan._meta?.timing_note}
            />
          ) : null}

          {selectedEvent.plan?.event_day_schedule.length ? (
            <Card>
              <CardHeader
                title="Event-day schedule"
                description="A minute-by-minute run sheet for the day itself."
              />
              <div className="divide-y divide-[var(--border)]">
                {selectedEvent.plan.event_day_schedule.map((slot, index) => (
                  <div
                    key={`${slot.start_time}-${index}`}
                    className="flex flex-wrap items-start gap-4 px-5 py-3"
                  >
                    <span className="w-28 shrink-0 font-mono text-xs text-ink-500">
                      {slot.start_time} - {slot.end_time}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium">{slot.activity}</p>
                      {slot.notes ? (
                        <p className="text-xs text-ink-500">{slot.notes}</p>
                      ) : null}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          ) : null}

          <ChecklistCard />
          <TimelineCard />
          <ExpensesCard />
        </>
      )}
    </div>
  );
}

