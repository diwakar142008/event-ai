/**
 * Typed client for the Eventora AI backend.
 *
 * The base URL is configurable via `NEXT_PUBLIC_API_URL` and defaults to the
 * local FastAPI dev server.
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;
  details: unknown;

  constructor(message: string, status: number, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {}),
      },
      cache: "no-store",
    });
  } catch (cause) {
    throw new ApiError(
      `Could not reach the Eventora API at ${API_BASE_URL}. Is the backend running?`,
      0,
      cause,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();
  let payload: unknown = null;
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = text;
    }
  }

  if (!response.ok) {
    const detail =
      (payload as { detail?: unknown } | null)?.detail ?? payload ?? response.statusText;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail
              .map((d) =>
                typeof d === "object" && d && "msg" in d
                  ? String((d as { msg: unknown }).msg)
                  : JSON.stringify(d),
              )
              .join("; ")
          : `Request failed with status ${response.status}`;
    throw new ApiError(message, response.status, payload);
  }

  return payload as T;
}

function jsonBody(data: unknown): string {
  return JSON.stringify(data);
}

// --------------------------------------------------------------------------- //
// Types
// --------------------------------------------------------------------------- //
export type EventType =
  | "wedding"
  | "birthday"
  | "anniversary"
  | "corporate"
  | "college"
  | "community";

export type CityTier = "tier1_metro" | "tier2_city" | "tier3_town";
export type VenueType =
  | "banquet_hall"
  | "hotel"
  | "outdoor_garden"
  | "farmhouse"
  | "banquet_resort"
  | "home";
export type ServiceLevel = "basic" | "standard" | "premium";
export type RiskLevel = "low" | "medium" | "high";

export interface EventPayload {
  name: string;
  event_type: EventType;
  event_date: string;
  city: CityTier;
  guest_count: number;
  budget: number;
  theme: string;
  style: string;
  preferences: string[];
  venue_type: VenueType;
  duration_hours: number;
  catering_level: ServiceLevel;
  decoration_level: ServiceLevel;
  photography: ServiceLevel;
}

export interface EventSummary extends EventPayload {
  id: string;
  created_at: string;
  updated_at: string;
}

export interface ChecklistItem {
  id: string;
  category: string;
  item: string;
  vendor_type: string;
  status: string;
  notes: string;
  estimated_cost: number;
  actual_cost: number | null;
}

export interface TimelineItem {
  id: string;
  phase: string;
  title: string;
  description: string;
  day_offset: number;
  owner: string;
  done: boolean;
}

export interface Expense {
  id: string;
  category: string;
  description: string;
  estimated: number;
  actual: number | null;
  paid: boolean;
}

export interface EventDetail extends EventSummary {
  plan: EventPlan | null;
  plan_source: "ai" | "fallback" | null;
  checklist: ChecklistItem[];
  timeline: TimelineItem[];
  expenses: Expense[];
}

export interface PlanOverview {
  concept: string;
  theme: string;
  style: string;
  color_palette: string[];
  highlights: string[];
}

export interface PlanBudgetLine {
  category: string;
  description: string;
  estimated_cost: number;
  priority: "must_have" | "should_have" | "nice_to_have";
}

export interface PlanChecklistItem {
  category: string;
  item: string;
  vendor_type: string;
  notes: string;
  estimated_cost: number;
}

export interface PlanTimelineItem {
  phase: "preparation" | "event_day";
  title: string;
  description: string;
  day_offset: number;
  owner: string;
  date?: string;
}

export interface PlanScheduleSlot {
  start_time: string;
  end_time: string;
  activity: string;
  notes: string;
}

export interface EventPlan {
  overview: PlanOverview;
  budget_breakdown: PlanBudgetLine[];
  checklist: PlanChecklistItem[];
  timeline: PlanTimelineItem[];
  event_day_schedule: PlanScheduleSlot[];
  tips: string[];
  contingency_note: string;
  assumptions: string[];
  _meta?: {
    provider?: string;
    model?: string;
    generated_at?: string;
    timing_note?: string;
    total_cost?: number;
    per_guest_cost?: number;
  };
}

export interface CostPrediction {
  predicted_cost: number;
  currency: string;
  lower_bound: number;
  upper_bound: number;
  per_guest_cost: number;
  confidence_note: string;
  budget: number | null;
  budget_gap: number | null;
  budget_status: "within_budget" | "over_budget" | "no_budget";
  budget_usage_pct: number | null;
  feature_importances: Record<string, number>;
  data_note: string;
}

export interface Recommendation {
  rank: number;
  name: string;
  category: string;
  score: number;
  reason: string;
  tags: string[];
  estimated_cost_per_guest: number | null;
  description?: string;
  price_band?: string;
}

export interface RecommendationResult {
  recommendations: Recommendation[];
  explanation: string;
  method_note: string;
}

export interface BudgetRisk {
  risk_level: RiskLevel;
  risk_label: string;
  confidence: number;
  reasons: string[];
  suggested_contingency: number;
  recommended_contingency_pct: number;
  saving_tips: string[];
  assumptions: string[];
  method_note: string;
}

export interface HealthStatus {
  status: string;
  version: string;
  environment: string;
  ai_provider: string;
  ai_configured: boolean;
  database: string;
  models_loaded: Record<string, boolean>;
  timestamp: string;
}

export interface Vocabulary {
  event_types: { value: EventType; label: string }[];
  city_tiers: { value: CityTier; label: string }[];
  venue_types: { value: VenueType; label: string }[];
  durations: number[];
  catering_levels: ServiceLevel[];
  decoration_levels: ServiceLevel[];
  photography_levels: ServiceLevel[];
  styles: string[];
  themes: string[];
  currency: string;
}

export interface MLMetrics {
  cost_model: Record<string, unknown>;
  recommendation_model: Record<string, unknown>;
  risk_model: Record<string, unknown>;
  generated_at: string;
  dataset_note: string;
}

// --------------------------------------------------------------------------- //
// Endpoints
// --------------------------------------------------------------------------- //
export const api = {
  health: () => request<HealthStatus>("/api/health"),

  vocabulary: () => request<Vocabulary>("/api/vocabulary"),

  listEvents: () => request<EventSummary[]>("/api/events"),

  getEvent: (id: string) => request<EventDetail>(`/api/events/${id}`),

  createEvent: (payload: EventPayload) =>
    request<EventSummary>("/api/events", {
      method: "POST",
      body: jsonBody(payload),
    }),

  updateEvent: (id: string, changes: Partial<EventPayload>) =>
    request<EventSummary>(`/api/events/${id}`, {
      method: "PATCH",
      body: jsonBody(changes),
    }),

  deleteEvent: (id: string) =>
    request<void>(`/api/events/${id}`, { method: "DELETE" }),

  // --- workspace ---
  addChecklistItem: (
    eventId: string,
    payload: {
      category: string;
      item: string;
      vendor_type?: string;
      notes?: string;
      estimated_cost?: number;
    },
  ) =>
    request<ChecklistItem>(`/api/events/${eventId}/checklist`, {
      method: "POST",
      body: jsonBody(payload),
    }),

  updateChecklistItem: (
    eventId: string,
    itemId: string,
    changes: Partial<{
      status: string;
      notes: string;
      estimated_cost: number;
      actual_cost: number;
      item: string;
      category: string;
      vendor_type: string;
    }>,
  ) =>
    request<ChecklistItem>(`/api/events/${eventId}/checklist/${itemId}`, {
      method: "PATCH",
      body: jsonBody(changes),
    }),

  deleteChecklistItem: (eventId: string, itemId: string) =>
    request<void>(`/api/events/${eventId}/checklist/${itemId}`, { method: "DELETE" }),

  addTimelineItem: (
    eventId: string,
    payload: {
      phase: "preparation" | "event_day";
      title: string;
      description?: string;
      day_offset: number;
      owner?: string;
    },
  ) =>
    request<TimelineItem>(`/api/events/${eventId}/timeline`, {
      method: "POST",
      body: jsonBody(payload),
    }),

  updateTimelineItem: (
    eventId: string,
    itemId: string,
    changes: Partial<{
      title: string;
      description: string;
      day_offset: number;
      owner: string;
      done: boolean;
    }>,
  ) =>
    request<TimelineItem>(`/api/events/${eventId}/timeline/${itemId}`, {
      method: "PATCH",
      body: jsonBody(changes),
    }),

  deleteTimelineItem: (eventId: string, itemId: string) =>
    request<void>(`/api/events/${eventId}/timeline/${itemId}`, { method: "DELETE" }),

  addExpense: (
    eventId: string,
    payload: {
      category: string;
      description: string;
      estimated?: number;
      actual?: number | null;
    },
  ) =>
    request<Expense>(`/api/events/${eventId}/expenses`, {
      method: "POST",
      body: jsonBody(payload),
    }),

  updateExpense: (
    eventId: string,
    expenseId: string,
    changes: Partial<{
      category: string;
      description: string;
      estimated: number;
      actual: number | null;
      paid: boolean;
    }>,
  ) =>
    request<Expense>(`/api/events/${eventId}/expenses/${expenseId}`, {
      method: "PATCH",
      body: jsonBody(changes),
    }),

  deleteExpense: (eventId: string, expenseId: string) =>
    request<void>(`/api/events/${eventId}/expenses/${expenseId}`, { method: "DELETE" }),

  // --- machine learning ---
  predictCost: (payload: {
    event_type: string;
    guest_count: number;
    city: string;
    venue_type: string;
    duration_hours: number;
    catering_level: string;
    decoration_level: string;
    photography: string;
    budget?: number | null;
  }) =>
    request<CostPrediction>("/api/ml/predict-cost", {
      method: "POST",
      body: jsonBody(payload),
    }),

  recommend: (payload: {
    event_type: string;
    budget: number;
    guest_count: number;
    preferences: string[];
    style: string;
    top_k?: number;
  }) =>
    request<RecommendationResult>("/api/ml/recommend", {
      method: "POST",
      body: jsonBody(payload),
    }),

  budgetRisk: (payload: {
    budget: number;
    predicted_cost: number;
    contingency_pct: number;
    guest_count: number;
  }) =>
    request<BudgetRisk>("/api/ml/budget-risk", {
      method: "POST",
      body: jsonBody(payload),
    }),

  mlMetrics: () => request<MLMetrics>("/api/ml/metrics"),

  // --- AI ---
  generatePlan: (payload: {
    event_id?: string;
    event?: EventPayload;
    extra_instructions?: string;
    regenerate?: boolean;
  }) =>
    request<{ plan: EventPlan; source: "ai" | "fallback"; provider: string; model: string; notice: string }>(
      "/api/ai/plan",
      { method: "POST", body: jsonBody(payload) },
    ),

  chat: (payload: {
    event_id?: string;
    message: string;
    history?: { role: string; content: string }[];
  }) =>
    request<{ reply: string; source: "ai" | "fallback"; provider: string; model: string; notice: string }>(
      "/api/ai/chat",
      { method: "POST", body: jsonBody(payload) },
    ),
};
