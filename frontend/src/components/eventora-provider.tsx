"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  api,
  ApiError,
  type EventDetail,
  type EventPayload,
  type EventSummary,
  type HealthStatus,
  type Vocabulary,
} from "@/lib/api";

interface EventoraContextValue {
  events: EventSummary[];
  selectedEventId: string | null;
  selectedEvent: EventDetail | null;
  vocabulary: Vocabulary | null;
  health: HealthStatus | null;
  loading: boolean;
  error: string | null;
  selectEvent: (id: string | null) => void;
  createEvent: (payload: EventPayload) => Promise<EventSummary>;
  updateEvent: (id: string, changes: Partial<EventPayload>) => Promise<void>;
  deleteEvent: (id: string) => Promise<void>;
  refresh: () => Promise<void>;
  refreshSelected: () => Promise<void>;
}

const EventoraContext = createContext<EventoraContextValue | null>(null);

const STORAGE_KEY = "eventora.selectedEventId";

export function EventoraProvider({ children }: { children: ReactNode }) {
  const [events, setEvents] = useState<EventSummary[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<EventDetail | null>(null);
  const [vocabulary, setVocabulary] = useState<Vocabulary | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadEvents = useCallback(async () => {
    const list = await api.listEvents();
    setEvents(list);
    return list;
  }, []);

  const loadSelected = useCallback(async (id: string | null) => {
    if (!id) {
      setSelectedEvent(null);
      return;
    }
    try {
      setSelectedEvent(await api.getEvent(id));
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setSelectedEvent(null);
        setSelectedEventId(null);
        if (typeof window !== "undefined") {
          window.localStorage.removeItem(STORAGE_KEY);
        }
        return;
      }
      throw err;
    }
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [list, vocab, status] = await Promise.all([
        api.listEvents(),
        api.vocabulary(),
        api.health().catch(() => null),
      ]);
      setEvents(list);
      setVocabulary(vocab);
      setHealth(status);

      let target = selectedEventId;
      if (!target || !list.some((event) => event.id === target)) {
        target = list.length > 0 ? list[0].id : null;
      }
      setSelectedEventId(target);
      if (target) {
        if (typeof window !== "undefined") {
          window.localStorage.setItem(STORAGE_KEY, target);
        }
        await loadSelected(target);
      } else {
        setSelectedEvent(null);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong while loading Eventora.",
      );
    } finally {
      setLoading(false);
    }
  }, [loadSelected, selectedEventId]);

  useEffect(() => {
    void refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const selectEvent = useCallback(
    (id: string | null) => {
      setSelectedEventId(id);
      if (typeof window !== "undefined") {
        if (id) window.localStorage.setItem(STORAGE_KEY, id);
        else window.localStorage.removeItem(STORAGE_KEY);
      }
      void loadSelected(id);
    },
    [loadSelected],
  );

  const createEvent = useCallback(
    async (payload: EventPayload) => {
      const created = await api.createEvent(payload);
      await loadEvents();
      selectEvent(created.id);
      return created;
    },
    [loadEvents, selectEvent],
  );

  const updateEvent = useCallback(
    async (id: string, changes: Partial<EventPayload>) => {
      await api.updateEvent(id, changes);
      await loadEvents();
      await loadSelected(id);
    },
    [loadEvents, loadSelected],
  );

  const deleteEvent = useCallback(
    async (id: string) => {
      await api.deleteEvent(id);
      const list = await loadEvents();
      const next = list.length > 0 ? list[0].id : null;
      setSelectedEventId(next);
      await loadSelected(next);
    },
    [loadEvents, loadSelected],
  );

  const refreshSelected = useCallback(async () => {
    await loadSelected(selectedEventId);
  }, [loadSelected, selectedEventId]);

  const value = useMemo<EventoraContextValue>(
    () => ({
      events,
      selectedEventId,
      selectedEvent,
      vocabulary,
      health,
      loading,
      error,
      selectEvent,
      createEvent,
      updateEvent,
      deleteEvent,
      refresh,
      refreshSelected,
    }),
    [
      events,
      selectedEventId,
      selectedEvent,
      vocabulary,
      health,
      loading,
      error,
      selectEvent,
      createEvent,
      updateEvent,
      deleteEvent,
      refresh,
      refreshSelected,
    ],
  );

  return (
    <EventoraContext.Provider value={value}>{children}</EventoraContext.Provider>
  );
}

export function useEventora(): EventoraContextValue {
  const context = useContext(EventoraContext);
  if (!context) {
    throw new Error("useEventora must be used inside <EventoraProvider>.");
  }
  return context;
}
