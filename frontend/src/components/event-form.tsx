"use client";

import { useState } from "react";

import { Button, Field, inputClass, selectClass } from "@/components/ui";
import { useEventora } from "@/components/eventora-provider";
import { PreferencesField } from "@/components/preferences-field";
import { formatINR } from "@/lib/format";
import type { EventPayload, EventType, ServiceLevel } from "@/lib/api";

const DEFAULT_FORM: EventPayload = {
  name: "",
  event_type: "wedding",
  event_date: "",
  city: "tier1_metro",
  guest_count: 150,
  budget: 500_000,
  theme: "Elegant",
  style: "Classic",
  preferences: [],
  venue_type: "banquet_hall",
  duration_hours: 5,
  catering_level: "standard",
  decoration_level: "standard",
  photography: "standard",
};

export function EventForm({
  onCreated,
  onCancel,
}: {
  onCreated?: () => void;
  onCancel?: () => void;
}) {
  const { vocabulary, createEvent } = useEventora();
  const [form, setForm] = useState<EventPayload>(DEFAULT_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const themes = vocabulary?.themes ?? [];
  const styles = vocabulary?.styles ?? [];
  const perGuest = form.guest_count > 0 ? form.budget / form.guest_count : 0;

  function update<K extends keyof EventPayload>(key: K, value: EventPayload[K]) {
    setForm((previous) => ({ ...previous, [key]: value }));
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!form.name.trim()) {
      setError("Give your event a name so you can find it later.");
      return;
    }
    if (!form.event_date) {
      setError("Pick the event date.");
      return;
    }

    setSubmitting(true);
    try {
      await createEvent({ ...form, name: form.name.trim() });
      setForm(DEFAULT_FORM);
      onCreated?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create the event.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Event name" required>
          <input
            className={inputClass}
            value={form.name}
            onChange={(event) => update("name", event.target.value)}
            placeholder="Meera & Arjun Wedding"
          />
        </Field>

        <Field label="Event type" required>
          <select
            className={selectClass}
            value={form.event_type}
            onChange={(event) => update("event_type", event.target.value as EventType)}
          >
            {(vocabulary?.event_types ?? []).map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Event date" required>
          <input
            type="date"
            className={inputClass}
            value={form.event_date}
            onChange={(event) => update("event_date", event.target.value)}
          />
        </Field>

        <Field label="City tier" required>
          <select
            className={selectClass}
            value={form.city}
            onChange={(event) =>
              update("city", event.target.value as EventPayload["city"])
            }
          >
            {(vocabulary?.city_tiers ?? []).map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </Field>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field
          label="Guest count"
          required
          hint={`${formatINR(perGuest)} per guest at this budget`}
        >
          <input
            type="number"
            min={1}
            max={2000}
            className={inputClass}
            value={form.guest_count}
            onChange={(event) =>
              update("guest_count", Math.max(1, Number(event.target.value) || 1))
            }
          />
        </Field>

        <Field label="Total budget (INR)" required>
          <input
            type="number"
            min={0}
            step={10000}
            className={inputClass}
            value={form.budget}
            onChange={(event) =>
              update("budget", Math.max(0, Number(event.target.value) || 0))
            }
          />
        </Field>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Theme" required>
          <select
            className={selectClass}
            value={form.theme}
            onChange={(event) => update("theme", event.target.value)}
          >
            {themes.map((theme) => (
              <option key={theme} value={theme}>
                {theme}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Style" required>
          <select
            className={selectClass}
            value={form.style}
            onChange={(event) => update("style", event.target.value)}
          >
            {styles.map((style) => (
              <option key={style} value={style}>
                {style}
              </option>
            ))}
          </select>
        </Field>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Venue type" required>
          <select
            className={selectClass}
            value={form.venue_type}
            onChange={(event) =>
              update("venue_type", event.target.value as EventPayload["venue_type"])
            }
          >
            {(vocabulary?.venue_types ?? []).map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Duration" required>
          <select
            className={selectClass}
            value={form.duration_hours}
            onChange={(event) => update("duration_hours", Number(event.target.value))}
          >
            {(vocabulary?.durations ?? [3, 4, 5, 6, 8]).map((hours) => (
              <option key={hours} value={hours}>
                {hours} hours
              </option>
            ))}
          </select>
        </Field>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {(
          [
            ["catering_level", "Catering"],
            ["decoration_level", "Decoration"],
            ["photography", "Photography"],
          ] as const
        ).map(([key, label]) => (
          <Field key={key} label={label} required>
            <select
              className={selectClass}
              value={form[key]}
              onChange={(event) => update(key, event.target.value as ServiceLevel)}
            >
              {(["basic", "standard", "premium"] as ServiceLevel[]).map((level) => (
                <option key={level} value={level}>
                  {level[0].toUpperCase() + level.slice(1)}
                </option>
              ))}
            </select>
          </Field>
        ))}
      </div>

      <PreferencesField
        preferences={form.preferences}
        onChange={(next) => update("preferences", next)}
      />

      {error ? (
        <p className="rounded-lg border border-brand-500/30 bg-brand-500/10 px-3 py-2 text-sm text-brand-700">
          {error}
        </p>
      ) : null}

      <div className="flex flex-wrap gap-2">
        <Button type="submit" disabled={submitting}>
          {submitting ? "Creating..." : "Create event"}
        </Button>
        {onCancel ? (
          <Button variant="ghost" onClick={onCancel} type="button">
            Cancel
          </Button>
        ) : null}
      </div>
    </form>
  );
}
