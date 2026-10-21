# Eventora AI - Smart Celebration Planner

A production-shaped full-stack application for planning celebrations end to end:
weddings, birthdays, anniversaries, corporate events, college events and
community celebrations.

Eventora combines **three executable machine-learning models** with an
**LLM-assisted planning layer** (and a deterministic fallback that needs no API
key), persists everything in **SQLite**, and ships with a **Next.js 16** frontend
and a **FastAPI** backend.

---

## Contents

- [What it does](#what-it-does)
- [Honesty about the data](#honesty-about-the-data)
- [Architecture](#architecture)
- [The three ML models](#the-three-ml-models)
- [AI layer and deterministic fallback](#ai-layer-and-deterministic-fallback)
- [Quick start](#quick-start)
- [API reference](#api-reference)
- [Testing](#testing)
- [Deployment](#deployment)
- [Repository layout](#repository-layout)
- [Design decisions and limitations](#design-decisions-and-limitations)

---

## What it does

| Capability | Implementation |
| --- | --- |
| **Cost estimation** | Random Forest regressor predicts total event cost from event type, guest count, city tier, venue, duration and three service tiers. Returns a point estimate plus an error band derived from training RMSE. |
| **Recommendations** | Content-based k-nearest-neighbours over a 31-item curated catalogue of themes, decoration packages, catering styles, activities and service bundles, re-ranked with explicit preference-token matching. |
| **Budget risk** | Decision Tree classifier labels a budget **low / medium / high** risk from the ratio of budget to estimated cost plus contingency, with plain-language reasons and targeted saving tips. |
| **AI event plan** | Produces a structured plan - creative overview, budget breakdown, 30+ checklist items, a 22-step timeline and a minute-by-minute event-day schedule - validated against a Pydantic schema. |
| **Planning workspace** | Interactive checklist with status tracking, timeline with completion toggles, and a budget tracker that compares estimates against actual spend. |
| **Assistant** | Context-aware chat about the selected event, with a rule-based answer path that works with no LLM provider. |

The five frontend tabs map onto those capabilities:

- **Overview** - create events, inspect event details, check system health.
- **Plan** - generate the AI plan; work the checklist, timeline and budget tracker.
- **Budget** - cost estimate, variance against budget, risk assessment, feature importances.
- **Insights** - ranked recommendations and the honest metrics behind all three models.
- **Assistant** - ask questions about the selected event.

---

## Honesty about the data

This matters enough to state up front, and the app repeats it in the UI.

**The cost model is trained on a synthetic dataset.** No openly licensed public
dataset of real-world event costs existed with the feature granularity this
project needs (category x guest count x city tier x venue x duration x service
tiers). Rather than scrape vendor websites with unclear licensing, or present
invented numbers as market data, the dataset is **generated from transparent,
documented cost rules** in `backend/app/ml/dataset.py`:

```
catering    = guests x per_guest(catering_level) x city_mult(city)
venue       = venue_base(venue_type) x city_mult(city) x (duration / 5)
decoration  = deco_base(decoration_level) x (1 + guests / 300)
photography = photo_base(photography)
fixed_block = (venue + decoration + photography) x event_type_multiplier
total       = (subtotal + 0.08 x subtotal) x lognormal_noise(sigma = 0.12)
```

Consequences, stated plainly:

- Reported metrics (R2 ~ 0.83, MAE ~ INR 46k) measure **fit to these rules**,
  not accuracy against real market prices.
- The budget-risk labels are **rule-derived, not human-annotated**. The tree
  learns to reproduce a stated policy, so its high accuracy means "the rule is
  faithfully implemented", not "we discovered independent risk patterns".
- The recommender has **no user-interaction data**, so it ranks by content
  similarity to a hand-curated catalogue. It does not learn personal preference.
- "Popularity" weights in the catalogue are editorial, not measured.

Every cost response carries a `data_note` with this caveat, the UI renders it
prominently, and the footer repeats it. **Treat the numbers as planning
guidance and confirm them with vendor quotes.**

---

## Architecture

```
prompt1/
|-- backend/                    FastAPI application
|   |-- app/
|   |   |-- main.py             App factory, CORS, routers, health check
|   |   |-- config.py           Pydantic settings from env / .env
|   |   |-- database/session.py SQLAlchemy engine + session
|   |   |-- models/event.py     ORM models (Event, Plan, Checklist, Timeline, Expense)
|   |   |-- schemas/
|   |   |   |-- event.py        Request/response models
|   |   |   |-- plan.py         Structured AI-plan schema
|   |   |   `-- vocabulary.py   Controlled vocabularies (single source of truth)
|   |   |-- repositories/       All database access lives here
|   |   |-- api/routes/         events.py, workspace.py, ml.py, ai.py
|   |   |-- ml/
|   |   |   |-- dataset.py      Synthetic cost dataset + cost rules
|   |   |   |-- train.py        Training pipeline for all three models
|   |   |   |-- risk.py         Decision Tree risk model
|   |   |   |-- recommendation.py  k-NN recommender
|   |   |   |-- catalogue*.py   Curated catalogue (31 items, 5 categories)
|   |   |   `-- catalogue_index.py
|   |   `-- services/
|   |       |-- ml_service.py   Model loading + inference wrappers
|   |       |-- ai_service.py   LLM calls, JSON extraction, fallback
|   |       |-- planner.py      Deterministic planner
|   |       `-- planner_templates.py / planner_timeline.py
|   |-- tests/                  pytest suite (38 tests)
|   `-- ml_artifacts/           Trained models (gitignored, regenerate)
|
`-- frontend/                   Next.js 16 (App Router, React 19, Tailwind v4)
    `-- src/
        |-- app/                /, /plan, /budget, /insights, /assistant
        |-- components/         Workspaces, cards, forms, provider
        `-- lib/                api.ts (typed client), format.ts
```

**Layering rule:** routers never touch SQLAlchemy models directly - they call
`app/repositories/`. Routers never load models directly - they call
`app/services/ml_service.py`. Swapping SQLite for Postgres, or the model
artifacts for a hosted endpoint, touches one layer.

---

## The three ML models

All three are real, executable `scikit-learn` pipelines. Artifacts are written
to `backend/ml_artifacts/` and are **gitignored** - regenerate with:

```bash
cd backend
python -m app.ml.train --all
```

### Model A - Cost prediction (Random Forest regressor)

| Property | Value |
| --- | --- |
| Algorithm | `RandomForestRegressor` (160 trees, max depth 18) |
| Features | 8: `event_type`, `guest_count`, `city`, `venue_type`, `duration_hours`, `catering_level`, `decoration_level`, `photography` |
| Preprocessing | `ColumnTransformer` -> `OneHotEncoder` (categorical) + `StandardScaler` (numeric) |
| Training rows | 4,000 synthetic, 80/20 split |
| **R2** | **0.8305** |
| **MAE** | **INR 46,382** |
| **RMSE** | **INR 73,395** |
| **MAPE** | **16.69%** |

The error band shown in the UI is +/- 1x training RMSE, which is a
residual-based estimate, not a confidence interval.

### Model B - Recommendations (content-based k-NN)

| Property | Value |
| --- | --- |
| Algorithm | `NearestNeighbors` (cosine distance, brute force) |
| Corpus | 31 curated catalogue items across 5 categories |
| Encoding | Event-type affinity, style affinity, price band, log-scaled cost-per-guest, popularity, plus a token-overlap block for preference matching |
| Re-ranking | Explicit bonus (max 0.15) for exact preference-token matches so a near-duplicate vector cannot bury a better match |

**No accuracy figure is reported, deliberately.** There is no held-out ground
truth ranking to score against, because no click or rating data was collected.
Reporting a made-up precision number would be worse than reporting nothing.

### Model C - Budget risk (Decision Tree classifier)

| Property | Value |
| --- | --- |
| Algorithm | `DecisionTreeClassifier` (max depth 8, min samples leaf 20, balanced) |
| Features | 7: `budget`, `predicted_cost`, `contingency_pct`, `guest_count`, `coverage_ratio`, `slack_amount`, `guest_cost_ratio` |
| Training rows | 6,000 synthetic, 80/20 stratified split |
| **Accuracy** | **1.0000** (see below) |
| Labels | `low` (coverage >= 1.25), `medium` (1.00 <= coverage < 1.25), `high` (coverage < 1.00) |

**Why accuracy is 1.0.** The target label is a deterministic function of
`coverage_ratio`, which is itself one of the input features. The tree is
therefore reproducing a documented rule. This is stated explicitly in the
`accuracy_note` field of the metrics response and in the UI, so nobody mistakes
it for evidence of predictive power on unseen market data.

### Reproducing and verifying

```bash
cd backend
python -m app.ml.train --all     # writes artifacts + metrics.json
curl http://127.0.0.1:8000/api/ml/metrics
```

---

## AI layer and deterministic fallback

The plan generator follows one rule: **never fail a request**.

1. If `AI_PROVIDER` is `none` or the API key is missing, the deterministic
   planner runs immediately.
2. If a provider call fails, times out, returns non-JSON, or returns JSON that
   does not satisfy `EventPlanSchema`, the deterministic planner runs instead.
3. The response always reports `source` (`"ai"` or `"fallback"`), `provider`,
   `model` and a human-readable `notice`, so the UI can state which path ran.

The deterministic planner is genuinely useful, not a stub: it uses the same cost
rules as the estimator, produces 31 checklist items, a 22-step timeline with
concrete dates, a duration-scaled event-day schedule, budget lines that sum to
the estimate, and tips that react to how much runway is left before the event.

Supported providers: **OpenAI** (`chat/completions`) and **Anthropic**
(`messages`), both called over plain HTTP with `httpx` so there is no heavy SDK
dependency. Model output is parsed with a tolerant JSON extractor (raw text,
then markdown fence, then outermost braces) before schema validation.

---

## Quick start

### Prerequisites

- Python 3.11+ (developed on 3.13)
- Node.js 20+ (developed on Node 20 with npm)

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt

# Copy and edit the environment file (optional - defaults work with no API key)
cp .env.example .env

# Train the three models (required before first run)
python -m app.ml.train --all

# Start the API
uvicorn app.main:app --reload --port 8000
```

The API is then at `http://127.0.0.1:8000` and interactive docs at
`http://127.0.0.1:8000/docs`.

Tables are created automatically on startup, so a fresh clone works with no
extra steps.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. The frontend reads the API location from
`NEXT_PUBLIC_API_URL` and defaults to `http://127.0.0.1:8000`.

```bash
# frontend/.env.local (optional)
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

### 3. Enable LLM planning (optional)

Without any key the app is fully functional using the deterministic planner.
To use a real model:

```bash
# backend/.env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

or

```bash
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-sonnet-latest
```

Restart the backend. `GET /api/health` reports `ai_configured: true` and the
Plan tab badge switches from "Deterministic fallback" to "AI generated".

### Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Comma-separated allowed origins |
| `DATABASE_URL` | *(empty - local SQLite)* | SQLAlchemy URL. Set for Postgres/Supabase |
| `AI_PROVIDER` | `none` | `openai`, `anthropic` or `none` |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | - / `gpt-4o-mini` | OpenAI credentials |
| `ANTHROPIC_API_KEY` / `ANTHROPIC_MODEL` | - / `claude-3-5-sonnet-latest` | Anthropic credentials |
| `AI_BASE_URL` | `https://api.openai.com/v1` | Override for compatible gateways |
| `AI_TIMEOUT_SECONDS` | `60` | Provider request timeout |
| `ML_MODEL_DIR` | `ml_artifacts` | Where trained artifacts live |
| `ENVIRONMENT` | `development` | Reported by `/api/health` |

**No secret is ever committed.** `.env` is gitignored; only `.env.example`
(with empty values) is tracked.

---

## API reference

Base URL: `http://127.0.0.1:8000`. Full interactive docs at `/docs`.

### Events

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/events` | List all events, ordered by date |
| `POST` | `/api/events` | Create an event (201) |
| `GET` | `/api/events/{id}` | Event with plan, checklist, timeline and expenses |
| `PATCH` | `/api/events/{id}` | Partial update of any event field |
| `DELETE` | `/api/events/{id}` | Delete an event and its dependents (204) |

### Workspace (all scoped to an event)

| Method | Path | Description |
| --- | --- | --- |
| `GET`/`POST` | `/api/events/{id}/checklist` | List / add checklist items |
| `PATCH`/`DELETE` | `/api/events/{id}/checklist/{item_id}` | Update status, notes, costs / remove |
| `GET`/`POST` | `/api/events/{id}/timeline` | List / add timeline items |
| `PATCH`/`DELETE` | `/api/events/{id}/timeline/{item_id}` | Update title, offset, `done` / remove |
| `GET`/`POST` | `/api/events/{id}/expenses` | List / add budget lines |
| `PATCH`/`DELETE` | `/api/events/{id}/expenses/{expense_id}` | Update actuals, `paid` / remove |

### Machine learning

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/ml/predict-cost` | Model A - cost estimate, error band, budget variance, feature importances |
| `POST` | `/api/ml/recommend` | Model B - ranked recommendations with reasons |
| `POST` | `/api/ml/budget-risk` | Model C - risk level, reasons, saving tips, assumptions |
| `GET` | `/api/ml/metrics` | Evaluation metrics for all three models |

### AI

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/ai/plan` | Generate a structured plan (`event_id` or inline `event`). Persists the plan and seeds the workspace. |
| `POST` | `/api/ai/chat` | Ask about an event. Returns `source`, `provider`, `model` and `notice`. |

### System

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/health` | Status, version, database state, AI configuration, model artifact status |
| `GET` | `/api/vocabulary` | Controlled vocabularies that drive the forms |

### Example

```bash
curl -X POST http://127.0.0.1:8000/api/ml/predict-cost \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "wedding",
    "guest_count": 300,
    "city": "tier1_metro",
    "venue_type": "hotel",
    "duration_hours": 6,
    "catering_level": "premium",
    "decoration_level": "premium",
    "photography": "premium",
    "budget": 2000000
  }'
```

```json
{
  "predicted_cost": 938458.94,
  "currency": "INR",
  "lower_bound": 865044.65,
  "upper_bound": 1011873.23,
  "per_guest_cost": 3128.2,
  "budget_status": "within_budget",
  "budget_gap": 1061541.06,
  "budget_usage_pct": 46.9,
  "data_note": "SYNTHETIC dataset generated from transparent cost rules ..."
}
```

---

## Testing

```bash
cd backend
python -m pytest tests -v
```

**Result: 38 passed.**

The suite covers:

- **`tests/test_api_events.py`** - event CRUD lifecycle, validation rejections
  (bad enum values, zero guests), 404 handling, plan generation seeding the
  workspace, and the deterministic fallback path.
- **`tests/test_api_ml.py`** - all three models through the API, guest-count
  scaling, budget variance, preference-aware recommendations, all three risk
  bands, metrics exposure, and request validation.
- **`tests/test_ml_units.py`** - dataset determinism, monotonicity of the cost
  rules with respect to guests, city tier and duration, component-to-total
  arithmetic, risk thresholds and contingency interaction, recommender
  determinism and ranking order, and schema conformance of the deterministic
  plan.

Tests run against a temporary SQLite database and never touch `eventora.db`.
The backend server is not required to be running.

Frontend checks:

```bash
cd frontend
npm run lint
npm run build     # production build with TypeScript checking
```

---

## Deployment

### Backend (Render / Railway / Fly.io / any container host)

The repository includes a ready-to-use `render.yaml` and a `Dockerfile`.

```bash
# Build
docker build -t eventora-api ./backend

# Run (SQLite is fine for a single instance)
docker run -p 8000:8000 -e AI_PROVIDER=openai -e OPENAI_API_KEY=... eventora-api
```

For a multi-instance deployment, point `DATABASE_URL` at Postgres (the models use
standard SQLAlchemy, so no code change is needed) and add
`psycopg[binary]` to `requirements.txt`.

**Platform steps**

1. Root directory: `backend`; build command: `pip install -r requirements.txt && python -m app.ml.train --all`;
   start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
2. Training must run before the app starts, because artifacts are gitignored.
3. Set `CORS_ORIGINS` to the exact frontend origin (no trailing slash).
4. Set `AI_PROVIDER` and the matching API key for LLM plans; omit them for the
   deterministic fallback.

### Frontend (Vercel / Netlify / any Node host)

```bash
cd frontend
npm run build
npm run start
```

Set `NEXT_PUBLIC_API_URL` to the deployed backend URL. The value is inlined at
build time, so rebuild after changing it.

### Health check

`GET /api/health` returns 200 with `status: "ok"`, the database state, the AI
configuration and whether each model artifact is present. Use it as the
platform health check and as a post-deploy smoke test.

### Security notes

- API keys are read from the environment, never logged, and never returned to
  the client.
- `.env` is gitignored; only `.env.example` (with empty values) is tracked.
- The CORS allowlist is explicit, not `*`.
- Every write endpoint validates input through Pydantic, with enum checks
  against the controlled vocabularies and numeric bounds on money and counts.

---

## Repository layout

```
backend/
  app/
    api/routes/       events.py workspace.py ml.py ai.py
    database/         session.py
    ml/               dataset.py train.py risk.py recommendation.py catalogue*.py
    models/           event.py
    repositories/     event_repo.py
    schemas/          event.py plan.py vocabulary.py
    services/         ml_service.py ai_service.py planner*.py
    config.py main.py
  tests/              test_api_events.py test_api_ml.py test_ml_units.py
  ml_artifacts/       (generated, gitignored)
  requirements.txt .env.example Dockerfile

frontend/
  src/app/            layout.tsx page.tsx globals.css plan/ budget/ insights/ assistant/
  src/components/     eventora-provider dashboard event-form event-selector
                      plan-workspace plan-overview-card checklist-card
                      timeline-card expenses-card budget-workspace
                      insights-workspace assistant-workspace ui format helpers
  src/lib/            api.ts format.ts
  package.json next.config.ts Dockerfile

render.yaml  README.md  .gitignore
```

### Repository size

The tracked repository is well under 10 MB. `node_modules/`, `.next/`,
`__pycache__/`, `*.db` and the trained `*.joblib` artifacts are all gitignored;
the ML artifacts (~5 MB) are regenerated by one command and are therefore
excluded from version control.

---

## Design decisions and limitations

### Decisions worth explaining

**Why a single controlled vocabulary module?**
`app/schemas/vocabulary.py` is the single source of truth for event types, city
tiers, venue types, service levels, styles and themes. The dataset generator,
the feature encoders, the Pydantic validators and the frontend form dropdowns
all read from it, so they cannot drift apart. The frontend also fetches it at
runtime from `/api/vocabulary`.

**Why is the cost breakdown returned as event-type-adjusted components?**
`compute_total_cost()` applies the event-type multiplier to the venue,
decoration and photography components before summing. This guarantees the
components always sum exactly to the total, so the budget tracker never shows
an unexplained remainder. A unit test asserts this.

**Why does the cost model predict on a DataFrame rather than a dict?**
The pipeline was fitted on a DataFrame, so `sklearn` validates feature names
and column order at inference time. Passing a bare dict raises a
feature-name error. The service builds a DataFrame with the exact training
column order.

**Why is the deterministic planner a real planner rather than a stub?**
Because the no-API-key path is the *default* path for anyone who clones this
repo. A stub would make the first run feel broken. The deterministic planner
shares the cost rules with the estimator, scales its checklist and timeline to
the event, dates the timeline from the event date, and scales the day schedule
to the requested duration.

**Why is the risk model's 1.0 accuracy not presented as a success?**
Because a rule-derived label with the rule's own input as a feature makes
accuracy trivially 1.0. The metrics response includes an `accuracy_note`
saying exactly that, and the UI shows it.

### Known limitations

| Area | Limitation |
| --- | --- |
| Cost data | Synthetic. No real vendor pricing is included. A production version would ingest a licensed price feed or vendor quotes. |
| Recommendations | Content-based only. There is no collaborative filtering because no interaction data is collected. Adding it would need an event of users. |
| Risk model | Rule-derived labels, not annotated real-world overruns. It enforces a stated policy rather than discovering risk. |
| Multi-user | No authentication. The API is single-tenant; anyone who can reach it can read and write every event. |
| Concurrent writes | SQLite with default settings suits a single instance. Postgres is the path to scale (and needs `psycopg` in requirements). |
| Timezone handling | Event dates are stored as plain dates; timeline dates are derived without timezone conversion. |
| LLM output | Plan generation is bounded by the provider's JSON reliability. Schema validation plus the deterministic fallback covers the failure mode, but a non-JSON reply always means the fallback path runs. |
| No rate limiting | The API has no built-in rate limiting; add one at the gateway for a public deployment. |

### What I would build next

1. A licensed vendor-price dataset to replace the synthetic one, with the cost
   model retrained and the same honesty caveats recomputed.
2. Event-level authentication (OAuth) and per-user event ownership.
3. Drag-and-drop timeline editing with vendor contact management.
4. A quote-comparison flow that records real vendor prices against the model's
   estimate, which would finally let the risk model learn from real outcomes.
5. A `/api/ml/retrain` admin endpoint that retrains and re-scores the models
   when new data lands.
