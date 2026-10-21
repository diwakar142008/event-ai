"use client";

import { useEffect, useRef, useState } from "react";

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
  inputClass,
} from "@/components/ui";
import { api } from "@/lib/api";

interface Turn {
  role: "user" | "assistant";
  content: string;
  source?: "ai" | "fallback";
}

const SUGGESTIONS = [
  "What is my estimated total cost?",
  "What should I book first?",
  "How do I reduce the budget?",
  "Walk me through the preparation timeline.",
];

export function AssistantWorkspace() {
  const { selectedEvent, selectedEventId } = useEventora();
  const [turns, setTurns] = useState<Turn[]>([]);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setTurns([]);
    setNotice(null);
  }, [selectedEventId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns]);

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || busy) return;

    setMessage("");
    setError(null);
    setBusy(true);

    const history = turns.map((turn) => ({
      role: turn.role,
      content: turn.content,
    }));

    setTurns((previous) => [...previous, { role: "user", content: trimmed }]);

    try {
      const result = await api.chat({
        event_id: selectedEventId ?? undefined,
        message: trimmed,
        history,
      });
      setTurns((previous) => [
        ...previous,
        { role: "assistant", content: result.reply, source: result.source },
      ]);
      setNotice(result.notice);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "The assistant is unavailable.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Assistant</h1>
          <p className="text-sm text-ink-500">
            Ask about cost, vendors, sequencing and budget trade-offs.
          </p>
        </div>
        <EventSelector />
      </div>

      <Card>
        <CardHeader
          title="Chat"
          description={
            selectedEvent
              ? `Answering about ${selectedEvent.name}.`
              : "No event selected - the assistant will give general guidance."
          }
        />

        <div className="min-h-[22rem] space-y-4 px-5 py-5">
          {turns.length === 0 ? (
            <EmptyState
              title="Ask anything about the plan"
              description="The assistant works with or without an LLM provider - without one it answers from the plan, the cost rules and the checklist."
            />
          ) : (
            turns.map((turn, index) => (
              <div
                key={`${turn.role}-${index}`}
                className={turn.role === "user" ? "flex justify-end" : "flex justify-start"}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-line ${
                    turn.role === "user"
                      ? "bg-brand-600 text-white"
                      : "border border-[var(--border)] bg-[var(--surface-muted)]"
                  }`}
                >
                  {turn.content}
                  {turn.source ? (
                    <span className="mt-2 block text-[10px] uppercase tracking-wide opacity-70">
                      {turn.source === "ai" ? "AI response" : "Rule-based response"}
                    </span>
                  ) : null}
                </div>
              </div>
            ))
          )}
          {busy ? <Spinner label="Thinking" /> : null}
          <div ref={bottomRef} />
        </div>

        {turns.length === 0 ? (
          <div className="flex flex-wrap gap-2 border-t border-[var(--border)] px-5 py-4">
            {SUGGESTIONS.map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => void send(suggestion)}
                className="rounded-full border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-1.5 text-xs text-ink-600 hover:border-brand-300 hover:text-brand-600"
              >
                {suggestion}
              </button>
            ))}
          </div>
        ) : null}

        <div className="space-y-3 border-t border-[var(--border)] px-5 py-4">
          {notice ? <Caveat>{notice}</Caveat> : null}
          {error ? <ErrorBanner message={error} /> : null}
          <div className="flex gap-2">
            <input
              className={inputClass}
              value={message}
              placeholder="Ask about your event..."
              onChange={(event) => setMessage(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  event.preventDefault();
                  void send(message);
                }
              }}
            />
            <Button onClick={() => void send(message)} disabled={busy || !message.trim()}>
              Send
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
