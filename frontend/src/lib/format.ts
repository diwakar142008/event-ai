/** Presentation helpers shared across the Eventora UI. */

const inrFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

const inrCompactFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  notation: "compact",
  maximumFractionDigits: 1,
});

export function formatINR(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return inrFormatter.format(value);
}

export function formatINRCompact(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  if (Math.abs(value) < 100000) return inrFormatter.format(value);
  return inrCompactFormatter.format(value);
}

export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("en-IN").format(value);
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Human label for a relative day offset (e.g. -14 -> "14 days before"). */
export function formatOffset(offset: number): string {
  if (offset === 0) return "Event day";
  const days = Math.abs(offset);
  const unit = days === 1 ? "day" : "days";
  return offset < 0 ? `${days} ${unit} before` : `${days} ${unit} after`;
}

export function daysUntil(value: string): number {
  const target = new Date(value);
  if (Number.isNaN(target.getTime())) return 0;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  target.setHours(0, 0, 0, 0);
  return Math.round((target.getTime() - today.getTime()) / 86_400_000);
}

export function titleCase(value: string): string {
  return value
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

export const CHECKLIST_STATUSES = [
  "pending",
  "contacted",
  "booked",
  "completed",
  "skipped",
] as const;

export function statusTone(status: string): string {
  switch (status) {
    case "completed":
      return "bg-sage-500/15 text-sage-500 border-sage-500/30";
    case "booked":
      return "bg-brand-500/15 text-brand-600 border-brand-500/30";
    case "contacted":
      return "bg-gold-500/15 text-gold-600 border-gold-500/30";
    case "skipped":
      return "bg-ink-400/15 text-ink-500 border-ink-400/30";
    default:
      return "bg-ink-100 text-ink-600 border-ink-200";
  }
}

export function riskTone(level: string): string {
  switch (level) {
    case "low":
      return "bg-sage-500/15 text-sage-500 border-sage-500/30";
    case "medium":
      return "bg-gold-500/15 text-gold-600 border-gold-500/30";
    default:
      return "bg-brand-500/15 text-brand-600 border-brand-500/30";
  }
}
