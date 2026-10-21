"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useEventora } from "@/components/eventora-provider";
import { EventSelector } from "@/components/event-selector";
import { PlanOverviewCard } from "@/components/plan-overview-card";
import { ChecklistCard } from "@/components/checklist-card";
import { TimelineCard } from "@/components/timeline-card";
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
import { api } from "@/lib/api";
import { formatINR, formatDate } from "@/lib/format";

const sections = ["Overview", "Timeline", "Checklist", "Vendors", "Assumptions"] as const;
type Section = (typeof sections)[number];

export function PlanWorkspace() {
  const { selectedEvent, selectedEventId, refreshSelected, loading } = useEventora();
  const [generating, setGenerating] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [source, setSource] = useState<"ai" | "fallback" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [instructions, setInstructions] = useState("");
  const [section, setSection] = useState<Section>("Overview");
  const generationLock = useRef(false);

  const generate = useCallback(
    async (regenerate: boolean) => {
      if (!selectedEventId) return;
      if (generationLock.current) return;
      if (regenerate && selectedEvent && (selectedEvent.checklist.length || selectedEvent.timeline.length || selectedEvent.expenses.length)) {
        const confirmed = window.confirm("Regenerating replaces this event’s checklist, timeline, and budget lines. Continue?");
        if (!confirmed) return;
      }
      generationLock.current = true;
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
        generationLock.current = false;
        setGenerating(false);
      }
    },
    [selectedEventId, selectedEvent, instructions, refreshSelected],
  );

  const completed = selectedEvent?.checklist.filter((item) => item.status === "completed").length ?? 0;
  const vendorTasks = useMemo(() => selectedEvent?.checklist.filter((item) => item.vendor_type) ?? [], [selectedEvent?.checklist]);

  // Generate a plan automatically the first time an event is opened here.
  useEffect(() => {
    if (
      selectedEventId &&
      selectedEvent &&
      !selectedEvent.plan &&
      !generationLock.current &&
      !error
    ) {
      const timer = window.setTimeout(() => void generate(false), 0);
      return () => window.clearTimeout(timer);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedEventId, selectedEvent?.plan]);

  if (loading) return <Spinner label="Loading the plan" />;

  return (
    <div className="space-y-5">
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
          <Card className="px-5 py-4">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-lg font-semibold">{selectedEvent.name}</h2>
                <p className="mt-1 text-sm text-ink-500">{formatDate(selectedEvent.event_date)} · {selectedEvent.guest_count} guests · Budget {formatINR(selectedEvent.budget)}</p>
              </div>
              <p className="text-sm text-ink-600">Plan progress: {completed} of {selectedEvent.checklist.length} tasks complete</p>
            </div>
          </Card>
          <nav aria-label="Planning sections" className="flex gap-2 overflow-x-auto border-b border-[var(--border)] pb-2">
            {sections.map((item) => <button key={item} type="button" onClick={() => setSection(item)} aria-current={section === item ? "page" : undefined} className={`shrink-0 rounded-lg px-3 py-2 text-sm font-medium focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-500 ${section === item ? "bg-brand-500/10 text-brand-700" : "text-ink-600 hover:bg-[var(--surface-muted)]"}`}>{item}</button>)}
          </nav>
          <Card>
            <CardHeader
              title="Generate the plan"
              description="The planner fills in the checklist, timeline and budget breakdown below. It works with or without an LLM API key."
            />
            <div className="space-y-4 px-5 py-5">
              <div className="flex flex-wrap items-center gap-2">
                <Button onClick={() => void generate(Boolean(selectedEvent.plan))} disabled={generating}>
                  {generating ? "Generating..." : selectedEvent.plan ? "Regenerate plan" : "Generate plan"}
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

          {section === "Overview" && selectedEvent.plan ? (
            <PlanOverviewCard
              concept={selectedEvent.plan.overview.concept}
              highlights={selectedEvent.plan.overview.highlights}
              palette={selectedEvent.plan.overview.color_palette}
              tips={selectedEvent.plan.tips}
              assumptions={[]}
              contingency={selectedEvent.plan.contingency_note}
              timingNote={selectedEvent.plan._meta?.timing_note}
            />
          ) : null}

          {section === "Assumptions" && selectedEvent.plan ? <Card><CardHeader title="Assumptions" description="Planning details inferred by the generator; verify these before booking."/><ul className="space-y-2 px-5 py-4">{selectedEvent.plan.assumptions.map((assumption, index) => <li key={`${index}-${assumption}`} className="text-sm text-ink-600">{assumption}</li>)}</ul></Card> : null}

          {section === "Vendors" ? <Card><CardHeader title="Vendor needs" description="Tasks that may need an external supplier."/>{vendorTasks.length ? <ul className="divide-y divide-[var(--border)]">{vendorTasks.map((task) => <li key={task.id} className="flex flex-wrap justify-between gap-2 px-5 py-3"><span className="text-sm">{task.item}</span><Badge className="border-[var(--border)] bg-[var(--surface-muted)] text-ink-500">{task.vendor_type}</Badge></li>)}</ul> : <div className="px-5 py-5 text-sm text-ink-500">No vendor assignments yet.</div>}</Card> : null}

          {section === "Timeline" && selectedEvent.plan?.event_day_schedule.length ? (
            <Card>
              <CardHeader
                title="Event-day schedule"
                description="A minute-by-minute run sheet for the day itself."
              />
              <div className="divide-y divide-[var(--border)]">
                {selectedEvent.plan.event_day_schedule.map((slot, index) => (
                  <div
                    key={`${slot.start_time}-${slot.activity}-${index}`}
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

          {section === "Timeline" ? <TimelineCard /> : null}
          {section === "Checklist" ? <ChecklistCard /> : null}
        </>
      )}
    </div>
  );
}

