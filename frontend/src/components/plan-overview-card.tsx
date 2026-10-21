"use client";

import { Card, CardHeader } from "@/components/ui";

export function PlanOverviewCard({
  concept,
  highlights,
  palette,
  tips,
  assumptions,
  contingency,
  timingNote,
}: {
  concept: string;
  highlights: string[];
  palette: string[];
  tips: string[];
  assumptions: string[];
  contingency: string;
  timingNote?: string;
}) {
  return (
    <Card>
      <CardHeader title="Plan overview" description={concept} />
      <div className="space-y-5 px-5 py-5">
        {palette.length > 0 ? (
          <div>
            <p className="mb-2 text-xs uppercase tracking-wide text-ink-500">
              Colour palette
            </p>
            <div className="flex flex-wrap gap-2">
              {palette.map((colour) => (
                <span
                  key={colour}
                  title={colour}
                  className="h-8 w-8 rounded-lg border border-[var(--border)]"
                  style={{ backgroundColor: colour }}
                />
              ))}
            </div>
          </div>
        ) : null}

        {highlights.length > 0 ? (
          <div>
            <p className="mb-2 text-xs uppercase tracking-wide text-ink-500">
              Highlights
            </p>
            <ul className="space-y-1.5">
              {highlights.map((highlight) => (
                <li key={highlight} className="flex gap-2 text-sm">
                  <span className="text-brand-500">&#9679;</span>
                  <span>{highlight}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {tips.length > 0 ? (
          <div>
            <p className="mb-2 text-xs uppercase tracking-wide text-ink-500">
              Planner tips
            </p>
            <ul className="space-y-1.5">
              {tips.map((tip) => (
                <li key={tip} className="flex gap-2 text-sm">
                  <span className="text-gold-500">&#8594;</span>
                  <span>{tip}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {timingNote ? (
          <p className="rounded-lg border border-brand-500/30 bg-brand-500/10 px-3 py-2 text-sm text-brand-700">
            {timingNote}
          </p>
        ) : null}

        {contingency ? (
          <p className="rounded-lg border border-sage-500/30 bg-sage-500/10 px-3 py-2 text-sm text-sage-500">
            {contingency}
          </p>
        ) : null}

        {assumptions.length > 0 ? (
          <details className="rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-2">
            <summary className="cursor-pointer text-sm font-medium">
              Assumptions ({assumptions.length})
            </summary>
            <ul className="mt-2 space-y-1.5">
              {assumptions.map((assumption) => (
                <li key={assumption} className="text-xs leading-relaxed text-ink-600">
                  &bull; {assumption}
                </li>
              ))}
            </ul>
          </details>
        ) : null}
      </div>
    </Card>
  );
}
