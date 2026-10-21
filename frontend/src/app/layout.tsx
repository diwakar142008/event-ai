import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Eventora AI — Smart Celebration Planner",
  description:
    "Plan weddings, birthdays, corporate and community events end to end: ML cost estimates, budget-risk analysis, tailored recommendations and AI-assisted planning.",
};

const NAV = [
  { href: "/", label: "Overview" },
  { href: "/plan", label: "Plan" },
  { href: "/budget", label: "Budget" },
  { href: "/insights", label: "Insights" },
  { href: "/assistant", label: "Assistant" },
];

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <header className="sticky top-0 z-40 border-b border-[var(--border)] bg-[var(--surface)]/85 backdrop-blur">
          <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
            <Link href="/" className="flex items-center gap-2.5">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-gold-500 text-lg shadow-sm">
                ✦
              </span>
              <span className="leading-tight">
                <span className="block text-sm font-semibold tracking-tight">
                  Eventora AI
                </span>
                <span className="block text-[11px] text-ink-500">
                  Smart Celebration Planner
                </span>
              </span>
            </Link>

            <nav className="flex flex-wrap items-center gap-1">
              {NAV.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="rounded-lg px-3 py-1.5 text-sm font-medium text-ink-600 transition-colors hover:bg-ink-100 hover:text-ink-900"
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>

        <main className="flex-1">{children}</main>

        <footer className="border-t border-[var(--border)] bg-[var(--surface)]">
          <div className="mx-auto max-w-7xl px-4 py-6 text-xs text-ink-500 sm:px-6">
            <p>
              Eventora AI — cost estimates come from a synthetic model trained on
              documented rules. Treat them as planning guidance and confirm with
              vendor quotes.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
