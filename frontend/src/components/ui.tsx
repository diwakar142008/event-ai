import type { ReactNode } from "react";

/** Surface card used for every panel in the app. */
export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-sm ${className}`}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-3 border-b border-[var(--border)] px-5 py-4">
      <div>
        <h2 className="text-base font-semibold tracking-tight">{title}</h2>
        {description ? (
          <p className="mt-1 text-sm text-ink-500">{description}</p>
        ) : null}
      </div>
      {action}
    </div>
  );
}

export function Badge({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${className}`}
    >
      {children}
    </span>
  );
}

export function Button({
  children,
  onClick,
  variant = "primary",
  type = "button",
  disabled = false,
  className = "",
  size = "md",
}: {
  children: ReactNode;
  onClick?: () => void;
  variant?: "primary" | "secondary" | "ghost" | "danger";
  type?: "button" | "submit";
  disabled?: boolean;
  className?: string;
  size?: "sm" | "md";
}) {
  const variants: Record<string, string> = {
    primary:
      "bg-brand-600 text-white hover:bg-brand-700 disabled:bg-brand-600/50 shadow-sm",
    secondary:
      "border border-[var(--border)] bg-[var(--surface)] text-ink-800 hover:bg-ink-50",
    ghost: "text-ink-600 hover:bg-ink-100",
    danger: "bg-brand-600/10 text-brand-600 hover:bg-brand-600/20",
  };
  const sizes: Record<string, string> = {
    sm: "px-3 py-1.5 text-xs",
    md: "px-4 py-2 text-sm",
  };
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-60 ${variants[variant]} ${sizes[size]} ${className}`}
    >
      {children}
    </button>
  );
}

export function Field({
  label,
  hint,
  children,
  required = false,
}: {
  label: string;
  hint?: string;
  children: ReactNode;
  required?: boolean;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 flex items-baseline justify-between gap-2">
        <span className="text-sm font-medium text-ink-800">
          {label}
          {required ? <span className="text-brand-500"> *</span> : null}
        </span>
        {hint ? <span className="text-xs text-ink-400">{hint}</span> : null}
      </span>
      {children}
    </label>
  );
}

export const inputClass =
  "w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm outline-none transition focus:border-brand-400 focus:ring-2 focus:ring-brand-500/20";

export const selectClass = `${inputClass} appearance-none bg-[right_0.6rem_center] bg-no-repeat pr-9`;

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 px-6 py-14 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-500/10 text-xl">
        ✨
      </div>
      <div>
        <p className="text-sm font-semibold">{title}</p>
        <p className="mx-auto mt-1 max-w-sm text-sm text-ink-500">{description}</p>
      </div>
      {action}
    </div>
  );
}

export function Spinner({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-10 text-sm text-ink-500">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-ink-300 border-t-brand-500" />
      {label}…
    </div>
  );
}

export function ErrorBanner({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-brand-500/30 bg-brand-500/10 px-4 py-3 text-sm text-brand-700">
      <span>{message}</span>
      {onRetry ? (
        <button
          onClick={onRetry}
          className="rounded-lg bg-brand-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-brand-700"
        >
          Retry
        </button>
      ) : null}
    </div>
  );
}

/** Inline caveat used wherever synthetic or rule-derived data is shown. */
export function Caveat({ children }: { children: ReactNode }) {
  return (
    <p className="rounded-lg border border-gold-500/30 bg-gold-500/10 px-3 py-2 text-xs leading-relaxed text-gold-600">
      {children}
    </p>
  );
}
