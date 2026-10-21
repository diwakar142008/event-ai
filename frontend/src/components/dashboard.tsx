"use client";

import Link from "next/link";
import { useState } from "react";

import { useEventora } from "@/components/eventora-provider";
import { EventForm } from "@/components/event-form";
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
import { daysUntil, formatDate, formatINR, titleCase } from "@/lib/format";

export function Dashboard() {
  const {
    events,
    selectedEvent,
    selectedEventId,
    health,
    loading,
    error,
    deleteEvent,
    refresh,
  } = useEventora();
  const [showForm, setShowForm] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  if (loading) {
    return <Spinner label="Loading your events" />;
  }

  return (
    <div className="space-y-8">
      <section className="celebration-wash overflow-hidden rounded-3xl border border-[var(--border)] px-6 py-10 sm:px-10">
        <div className="max-w-3xl">
          <Badge className="border-brand-500/30 bg-brand-500/10 text-brand-700">
            Smart Celebration Planner
          </Badge>
          <h1 className="mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">
            Plan the celebration, not the guesswork.
          </h1>
          <p className="mt-3 max-w-2xl text-ink-600">
            Eventora combines three machine-learning models with AI-assisted
            planning to give you a cost range, a budget-risk read, a practical
            checklist and a day-of schedule for any event.
          </p>
          <div className="mt-6 flex flex-wrap gap-2">
            <Button onClick={() => setShowForm((value) => !value)}>
              {showForm ? "Close form" : "Create an event"}
            </Button>
            <Link
              href="/plan"
              className="inline-flex items-center rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-2 text-sm font-medium transition-colors hover:bg-ink-50"
            >
              Open the planner
            </Link>
          </div>
        </div>
      </section>

      {error ? <ErrorBanner message={error} onRetry={() => void refresh()} /> : null}

      {showForm ? (
        <Card>
          <CardHeader
            title="New event"
            description="Tell us the basics - you can refine everything later."
          />
          <div className="px-5 py-5">
            <EventForm
              onCreated={() => setShowForm(false)}
              onCancel={() => setShowForm(false)}
            />
          </div>
        </Card>
      ) : null}

      <Card>
        <CardHeader
          title="Your events"
          description={
            events.length > 0
              ? "Select an event to work on it across every tab."
              : "Create your first event to get started."
          }
        />
        <div className="px-5 py-5">
          {events.length === 0 ? (
            <EmptyState
              title="No events yet"
              description="Create an event and Eventora will estimate the cost, assess your budget risk and draft a full plan."
              action={
                <Button onClick={() => setShowForm(true)}>Create an event</Button>
              }
            />
          ) : (
            <EventSelector />
          )}
        </div>
      </Card>

      {selectedEvent ? (
        <Card>
          <CardHeader
            title={selectedEvent.name}
            description={`${titleCase(selectedEvent.event_type)} on ${formatDate(selectedEvent.event_date)}`}
            action={
              confirmDelete ? (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-ink-500">Delete this event?</span>
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={async () => {
                      setConfirmDelete(false);
                      await deleteEvent(selectedEvent.id);
                    }}
                  >
                    Yes, delete
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => setConfirmDelete(false)}>
                    Cancel
                  </Button>
                </div>
              ) : (
                <Button variant="danger" size="sm" onClick={() => setConfirmDelete(true)}>
                  Delete
                </Button>
              )
            }
          />

          <div className="grid gap-4 px-5 py-5 sm:grid-cols-2 lg:grid-cols-4">
            <Stat label="Guests" value={String(selectedEvent.guest_count)} />
            <Stat label="Budget" value={formatINR(selectedEvent.budget)} />
            <Stat
              label="Days to go"
              value={String(Math.max(0, daysUntil(selectedEvent.event_date)))}
            />
            <Stat label="Checklist items" value={String(selectedEvent.checklist.length)} />
          </div>

          <div className="border-t border-[var(--border)] px-5 py-5">
            <dl className="grid gap-x-6 gap-y-3 sm:grid-cols-2 lg:grid-cols-3">
              <Detail label="Theme" value={selectedEvent.theme} />
              <Detail label="Style" value={selectedEvent.style} />
              <Detail label="Venue" value={titleCase(selectedEvent.venue_type)} />
              <Detail label="City tier" value={titleCase(selectedEvent.city)} />
              <Detail
                label="Duration"
                value={`${selectedEvent.duration_hours} hours`}
              />
              <Detail
                label="Catering"
                value={titleCase(selectedEvent.catering_level)}
              />
              <Detail
                label="Decoration"
                value={titleCase(selectedEvent.decoration_level)}
              />
              <Detail
                label="Photography"
                value={titleCase(selectedEvent.photography)}
              />
              <Detail
                label="Preferences"
                value={
                  selectedEvent.preferences.length > 0
                    ? selectedEvent.preferences.join(", ")
                    : "None stated"
                }
              />
            </dl>

            {selectedEvent.preferences.length > 0 ? (
              <div className="mt-4 flex flex-wrap gap-1.5">
                {selectedEvent.preferences.map((preference) => (
                  <Badge
                    key={preference}
                    className="border-brand-500/30 bg-brand-500/10 text-brand-700"
                  >
                    {preference}
                  </Badge>
                ))}
              </div>
            ) : null}
          </div>
        </Card>
      ) : null}

      {health ? (
        <Card>
          <CardHeader
            title="System status"
            description="Backend, database and model availability."
          />
          <div className="grid gap-4 px-5 py-5 sm:grid-cols-2 lg:grid-cols-4">
            <Stat
              label="API"
              value={health.status}
              hint={`v${health.version} | ${health.environment}`}
            />
            <Stat label="Database" value={health.database} />
            <Stat
              label="AI provider"
              value={health.ai_configured ? health.ai_provider : "deterministic fallback"}
              hint={health.ai_configured ? undefined : "Set AI_PROVIDER and an API key to enable LLM plans"}
            />
            <Stat
              label="Cost model"
              value={health.models_loaded.cost_model ? "loaded" : "missing"}
            />
          </div>
        </Card>
      ) : null}
    </div>
  );
}

function Stat({
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
      <p className="mt-1 text-lg font-semibold capitalize">{value}</p>
      {hint ? <p className="mt-0.5 text-xs text-ink-400">{hint}</p> : null}
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-ink-500">{label}</dt>
      <dd className="mt-0.5 text-sm">{value}</dd>
    </div>
  );
}
