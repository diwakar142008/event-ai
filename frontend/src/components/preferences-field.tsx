"use client";

import { useState } from "react";

import { Button, Field, inputClass } from "@/components/ui";

const PREFERENCE_SUGGESTIONS = [
  "outdoor ceremony",
  "live music",
  "vegetarian",
  "traditional",
  "minimal decor",
  "photography",
  "dance floor",
  "mehndi",
  "cocktail hour",
  "sustainability",
  "kid-friendly",
  "destination",
];

export function PreferencesField({
  preferences,
  onChange,
}: {
  preferences: string[];
  onChange: (next: string[]) => void;
}) {
  const [draft, setDraft] = useState("");

  function add(raw: string) {
    const value = raw.trim().toLowerCase();
    if (!value) return;
    if (preferences.includes(value)) return;
    if (preferences.length >= 20) return;
    onChange([...preferences, value]);
    setDraft("");
  }

  return (
    <Field
      label="Preferences"
      hint="These steer the AI plan and the recommendation engine"
    >
      <div className="flex gap-2">
        <input
          className={inputClass}
          value={draft}
          placeholder="e.g. outdoor ceremony"
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              add(draft);
            }
          }}
        />
        <Button variant="secondary" onClick={() => add(draft)} type="button">
          Add
        </Button>
      </div>

      {preferences.length > 0 ? (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {preferences.map((preference) => (
            <button
              key={preference}
              type="button"
              onClick={() => onChange(preferences.filter((item) => item !== preference))}
              className="inline-flex items-center gap-1.5 rounded-full border border-brand-500/30 bg-brand-500/10 px-2.5 py-1 text-xs font-medium text-brand-700 hover:bg-brand-500/20"
            >
              {preference}
              <span aria-hidden>×</span>
            </button>
          ))}
        </div>
      ) : null}

      <div className="mt-2 flex flex-wrap gap-1.5">
        {PREFERENCE_SUGGESTIONS.filter(
          (suggestion) => !preferences.includes(suggestion),
        )
          .slice(0, 8)
          .map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              onClick={() => add(suggestion)}
              className="rounded-full border border-[var(--border)] bg-[var(--surface-muted)] px-2.5 py-1 text-xs text-ink-600 hover:border-brand-300 hover:text-brand-600"
            >
              + {suggestion}
            </button>
          ))}
      </div>
    </Field>
  );
}
