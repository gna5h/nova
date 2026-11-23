# Architecture — Data Analyst AI Dev Assistant

> A web app that automates the repetitive parts of data analysis (profiling, cleaning, aggregation, statistical testing, reporting). Users either **ask in plain language**, and the AI builds a step-by-step plan, or **use the guided wizard** directly. Each step returns an output: a cleaned file, a result table, a test result or a report.

**Status:** v0.1 (architecture agreed, before Step 0)
**Owner:** _your name_
**Purpose:** Portfolio project; tested on real-world public datasets.

---

## 1. Goals and non-goals

### Goals
- Automate repetitive analyst work: profiling, cleaning, aggregation, hypothesis tests, report export.
- Two ways in: **Chat** (natural language → plan) and **Wizard** (manual step selection). Both produce the same `Plan` object.
- **Transparent and reproducible:** every change is logged, and any analysis can be exported as a Python script.
- **Correct:** all numbers come from deterministic code and are checked against hand-computed golden answers.
- **Public demo:** recruiters can try it in one click with sample datasets and no sign-up.

### Non-goals (for now)
- User accounts or saved projects (sessions are temporary).
- Big-data scale (target: files ≤ 10 MB, roughly 100k rows).
- Creating native, interactive Excel PivotTables (we export static result tables).
- Machine-learning model training.

---

## 2. Core principles

1. **Everything is a Step.** Every feature implements the same interface (§5). Adding a feature means adding one file and registering it.
2. **Code computes, AI communicates.** The LLM plans, explains and summarizes. It **never** produces numbers. All math uses pandas/scipy/statsmodels.
3. **The AI sees metadata, not data.** Only profile summaries (column names, types, issue counts, a few example values) are sent to the LLM, never full rows.
4. **The backend owns the contract.** FastAPI's OpenAPI schema is the source of truth, and the frontend's TypeScript client is generated from it.
5. **The schema drives the UI.** Wizard forms are rendered from each Step's Pydantic parameter schema, so new Steps need no frontend changes.
6. **The engine works without AI.** If the LLM is unavailable or out of quota, the manual wizard still works.
7. **Data is immutable.** Steps never modify data in place. Each run creates a new data version.

---

## 3. Tech stack

| Area | Choice | Notes |
|---|---|---|
| Frontend | **Next.js (App Router) + React + TypeScript** | Hosted on **Vercel** |
| UI kit | Tailwind CSS + shadcn/ui | Optional; matches typical portfolio setups |
| Data tables | TanStack Table | Virtualized for large previews |
| Charts | Recharts (or Vega-Lite) | Chart specs come from the backend |
| Forms | react-jsonschema-form (or a custom renderer) | Renders Step params from JSON Schema |
| Backend | **Python 3.12 + FastAPI** | Hosted on **Hugging Face Spaces (Docker)** |
| Schemas | **Pydantic v2** | Step params, results, API models |
| Data | **pandas** (+ optional **DuckDB/polars** later) | |
| Stats | **scipy**, **statsmodels** | t-tests, ANOVA, chi-square, correlation |
| Excel I/O | **openpyxl** | Read XLSX, write multi-sheet reports |
| LLM | **Gemini (free tier)** primary, **Groq (free tier)** fallback | Both via an OpenAI-compatible client |
| Typed client | openapi-typescript (+ openapi-fetch) | Generated from FastAPI's `/openapi.json` |
| Testing | pytest (backend), Vitest + Playwright (frontend) | Golden tests from the bank churn case study |
| Tooling | uv (Python deps), pnpm (JS), ruff + mypy, ESLint + Prettier | |
| CI | GitHub Actions | Lint, test, type-check, client-generation check |

---

## 4. System overview

```
┌──────────────── Vercel ────────────────┐
│  Next.js frontend                      │
│  • Chat panel     • Wizard cards       │
│  • Data preview   • Charts • Downloads │
└───────────────────┬────────────────────┘
                    │ HTTPS, typed client (generated)
┌───────────────────▼─────────── Hugging Face Space (Docker) ─┐
│  FastAPI                                                    │
│  ├── routes/    HTTP layer: validation, limits, errors      │
│  ├── ai/        planner + summarizer + LLM client  ─────────────► Gemini / Groq
│  ├── session/   data versions, step history, TTL cleanup    │
│  └── core/      Step registry + Steps (pandas/scipy)        │
└─────────────────────────────────────────────────────────────┘
```

### Layer dependencies (strict, top → down only)

```
routes  →  ai  →  session  →  core
routes  →  session  →  core
```
- `core` imports nothing from the other layers. It is pure Python and fully unit-testable.
- `ai` may read the Step registry and profile results, but it never calls pandas directly.
- `routes` contains no business logic. It only translates HTTP requests to service calls.

---

## 5. The Step contract (core)

Every feature is a Step. This is the most important part of the codebase.

```python
# core/step.py  (sketch, not final code)
class StepParams(BaseModel):            # each Step subclasses this
    ...

class StepResult(BaseModel):
    data: pd.DataFrame | None           # new dataset version (None if unchanged)
    tables: list[ResultTable]           # e.g. pivot output, test output
    charts: list[ChartSpec]             # backend-defined chart specs
    files: list[OutputFile]             # downloadable outputs (csv/xlsx)
    change_log: list[ChangeEntry]       # row/column-level changes made
    facts: dict[str, Any]               # computed numbers for the AI summarizer
    warnings: list[str]

class Step(Protocol):
    id: str                             # "clean.impute"
    category: Literal["io","profile","clean","aggregate","stats","export"]
    title: str                          # "Fill missing values"
    description: str                    # used by the UI and the AI planner
    Params: type[StepParams]            # Pydantic model → JSON Schema for the wizard
    def run(self, df: pd.DataFrame, params: StepParams) -> StepResult: ...
```

### Registry
```python
# core/registry.py
@register_step
class ImputeStep: ...
```
- `registry.list()` returns the metadata and JSON Schemas for all Steps (served at `GET /steps`).
- `registry.get(id)` returns a Step instance.
- The AI planner receives the same catalog, so it can only propose Steps that exist.

### Checklist for adding a Step
1. Create `core/steps/<category>/<name>.py` with `Params` + `run()`.
2. Decorate it with `@register_step`.
3. Add unit tests in `tests/core/steps/`.
4. If it relates to the case study, add or extend a golden test.
5. Nothing else: the API, wizard and planner pick it up automatically.

---

## 6. Step catalog (planned)

| Category | Step id | Output |
|---|---|---|
| io | `io.load` | Parsed dataset (CSV/XLSX), detected types and encoding |
| profile | `profile.summary` | Per-column report: type, missing, unique, invalid values, outliers, duplicates |
| clean | `clean.impute` | Fill missing values (mean/median/mode/constant) → cleaned file + change log |
| clean | `clean.fix_invalid` | Replace values that fail type/range rules (e.g. text in a numeric column, negatives) |
| clean | `clean.convert_type` | Convert column types (number, date, category) |
| clean | `clean.standardize_categories` | Unify labels ("FR", "france" → "France") |
| clean | `clean.drop_duplicates` / `clean.drop_rows` | |
| aggregate | `aggregate.pivot` | Group by rows/columns → mean/sum/count/rate table + chart |
| stats | `stats.ttest_ind` | Two-sample t-test (equal or unequal variance, matching Excel ToolPak) |
| stats | `stats.anova_oneway` | One-way ANOVA (matching ToolPak "Anova: Single Factor") |
| stats | `stats.chi_square` | Test of independence (later) |
| stats | `stats.correlation` | Pearson/Spearman matrix (later) |
| export | `export.dataset` | Current data version as CSV/XLSX |
| export | `export.report` | Multi-sheet XLSX: one sheet per result, with summaries |

### Cleaning rules (important detail)
- "Invalid" is defined by explicit rules per column type: non-numeric text in a numeric column, out-of-range values, values matching configured missing tokens (`"", "N/A", "-", "?", "null"`).
- **Imputation statistics are computed from valid values only**: missing and invalid values are excluded *before* the mean is calculated.
- Every replacement is written to `change_log` with: row, column, old value, new value, reason.

---

## 7. Session layer

A session is one analysis on one uploaded dataset.

```
Session
├── id, created_at, expires_at (TTL ≈ 60 min)
├── versions: [v0 raw, v1, v2, ...]   # stored as Parquet on temp disk
├── history:  [StepRun(step_id, params, input_version, output_version, result_meta)]
└── current_version
```

- **Storage:** Parquet files in a temp directory plus an in-memory index. Free-tier disks don't persist, so sessions are temporary by design.
- **Cleanup:** a background task deletes expired sessions.
- **Undo:** move `current_version` back to an earlier version.
- **Reproducibility:** `GET /sessions/{id}/script` turns the history into a runnable pandas script. This is a portfolio highlight.

---

## 8. AI layer

### Components
- `ai/llm_client.py`: one client for OpenAI-compatible endpoints. The provider, model and key come from env vars. It falls back from Gemini to Groq, with timeouts and retries.
- `ai/planner.py`: (user message + dataset profile + Step catalog) → **Plan** (structured output, validated with Pydantic).
- `ai/summarizer.py`: (StepResult.facts + question) → plain-language findings. It is told to use only the numbers it is given.
- `ai/prompts/`: versioned prompt templates.

### Plan object (shared by chat and wizard)
```python
class PlanStep(BaseModel):
    step_id: str            # must exist in the registry
    params: dict            # validated against that Step's Params schema
    reason: str             # "Salary has 12 missing values"

class Plan(BaseModel):
    goal: str
    steps: list[PlanStep]
```
- Chat: the LLM produces the `Plan`.
- Wizard: the user builds the `Plan` by hand.
- In both cases, every `PlanStep` is validated against the registry **before** the user sees it. Invalid suggestions are dropped or repaired.

### Safety and cost rules
- Never send raw rows. At most a few example values per column, from the profile.
- Cache planner responses by (profile hash, message).
- Per-IP daily limit on AI calls. Show a clear message when the quota is used up, and the wizard keeps working.
- Model names live in config, not code, because free-tier model lists change often.

---

## 9. API (v1)

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness check (also used to wake the Space) |
| GET | `/steps` | Step catalog with JSON Schemas |
| GET | `/samples` | List of bundled demo datasets |
| POST | `/sessions` | Upload a file **or** choose a sample → session + v0 + auto profile |
| GET | `/sessions/{id}` | Session state: versions, history |
| GET | `/sessions/{id}/preview?version=&page=` | Paginated data preview |
| POST | `/sessions/{id}/plan` | `{message}` → `Plan` (AI) |
| POST | `/sessions/{id}/run` | `{step_id, params}` → `StepResult` metadata (+ new version) |
| POST | `/sessions/{id}/undo` | Revert to the previous version |
| GET | `/sessions/{id}/files/{file_id}` | Download an output file |
| GET | `/sessions/{id}/script` | Export the analysis as a Python script |

- Errors use one shared shape: `{ "error": { "code", "message", "details" } }`.
- Limits: max upload 10 MB; allowed types `.csv`, `.xlsx`; per-IP rate limit.
- CORS: allow only the Vercel domain (+ localhost in dev).

---

## 10. Frontend

### Pages
- `/`: landing page with what it does, a demo GIF, "Try with sample data" and "Upload your file".
- `/workspace/[sessionId]`: the main app.

### Workspace layout
```
┌──────────────┬───────────────────────────────────┐
│  Chat panel  │  Wizard / Plan cards               │
│              │  ┌ Step 1: Fill missing Salary ┐   │
│  "Clean this │  │ strategy: [mean ▾]  [Run]   │   │
│   and test   │  └─────────────────────────────┘   │
│   salary vs  │  Results: table · chart · files    │
│   churn"     │  Data preview (current version)    │
└──────────────┴───────────────────────────────────┘
```

### Key components
`ChatPanel`, `PlanView`, `StepCard` (form generated from JSON Schema), `ResultTable`, `ChartView`, `ChangeLogView`, `DataPreview`, `VersionTimeline`, `DownloadButton`, `WakeUpBanner`.

### Conventions
- All API calls go through the generated client in `lib/api/`. No hand-written `fetch` to the backend.
- Server state is managed with TanStack Query.
- No secrets in the frontend. The only env var is `NEXT_PUBLIC_API_URL`.

---

## 11. Deployment

| Piece | Host | Notes |
|---|---|---|
| Frontend | Vercel | Same account as your portfolio; link to it from there |
| Backend | Hugging Face Space (Docker SDK) | Sleeps when idle → the frontend pings `/health` on load and shows a wake-up banner |
| LLM | Gemini API (free tier), Groq (free tier) | Keys stored as HF Space secrets |

### Environment variables (backend)
`LLM_PRIMARY_PROVIDER`, `LLM_PRIMARY_MODEL`, `GEMINI_API_KEY`, `LLM_FALLBACK_PROVIDER`, `LLM_FALLBACK_MODEL`, `GROQ_API_KEY`, `ALLOWED_ORIGINS`, `MAX_UPLOAD_MB`, `SESSION_TTL_MINUTES`, `AI_DAILY_LIMIT_PER_IP`.

### Pipeline
1. Push to `main` → GitHub Actions: lint, type-check, tests, check that the generated client is up to date.
2. Vercel deploys `apps/web` automatically.
3. The `apps/api` Docker image deploys to the HF Space (via GitHub Action or git push to the Space repo).

---

## 12. Testing strategy

| Level | What | Tool |
|---|---|---|
| Unit | Each Step in isolation, with small hand-built DataFrames | pytest |
| **Golden** | The bank churn case study end to end; outputs must match hand-computed Excel answers within tolerance | pytest |
| API | Routes with a test client; upload → run → download | pytest + httpx |
| AI | Planner output always validates against the registry; prompts tested with recorded responses (no live calls in CI) | pytest |
| Frontend | Components (Vitest) and one happy-path flow (Playwright) | Vitest, Playwright |

### Golden test cases (from the case study)
- Mean imputation for `EstimatedSalary` (missing) and `Balance` (invalid).
- Pivot: avg CreditScore by Geography; avg Balance by Geography × Gender; count IsActiveMember × HasCrCard; churn rate by NumOfProducts; avg CreditScore by Tenure × Churn.
- t-test: EstimatedSalary by Churn (ToolPak variant to be confirmed).
- ANOVA: CreditScore by Geography.

---

## 13. Repository structure

```
analyst-assistant/
├── apps/
│   ├── web/                      # Next.js → Vercel
│   │   ├── app/                  # routes: /, /workspace/[id]
│   │   ├── components/
│   │   ├── lib/api/              # generated typed client
│   │   └── package.json
│   └── api/                      # FastAPI → HF Space
│       ├── core/
│       │   ├── step.py           # Step protocol, StepResult, etc.
│       │   ├── registry.py
│       │   └── steps/
│       │       ├── io/  profile/  clean/  aggregate/  stats/  export/
│       ├── session/
│       ├── ai/
│       │   ├── llm_client.py  planner.py  summarizer.py
│       │   └── prompts/
│       ├── routes/
│       ├── main.py
│       ├── tests/
│       │   ├── core/  api/  ai/
│       │   └── golden/           # case-study data + expected answers
│       ├── Dockerfile
│       └── pyproject.toml
├── samples/                      # demo datasets (bank churn + messy public sets)
├── docs/
│   ├── ARCHITECTURE.md
│   └── decisions/                # short ADRs for key choices
├── .github/workflows/
└── README.md
```

---

## 14. Roadmap

| # | Milestone | Done when |
|---|---|---|
| 0 | **Skeleton** | Monorepo; Step protocol + registry + StepResult; session store; `/health` and `/steps`; Next.js page shows the backend status; **both apps deployed** |
| 1 | Loader + Profiler | Upload or choose a sample → profile report shown in the UI |
| 2 | Cleaning | Impute / fix invalid / convert types; cleaned file download + change log; golden test for imputation passes |
| 3 | Aggregation | Pivot Step + table + chart; 5 golden pivot tests pass |
| 4 | Stats | t-test + ANOVA matching ToolPak output; golden tests pass |
| 5 | AI Planner | Chat → validated Plan → wizard cards |
| 6 | Summaries + Report | AI findings from facts; multi-sheet XLSX export; script export |
| 7 | Polish | Landing page, demo GIF, README, rate limits, error states, linked from the portfolio |

---

## 15. Open decisions

- [ ] t-test variant: equal vs. unequal variance, to match the course's expected answer (decide in milestone 4).
- [ ] Chart library: Recharts vs. Vega-Lite.
- [ ] Form rendering: react-jsonschema-form vs. a lightweight custom renderer.
- [ ] Whether to add "bring your own API key" for heavy users.

---

## 16. Decision log

| Date | Decision | Why |
|---|---|---|
| 2026-11-23 | Next.js frontend + FastAPI backend | Existing React/Vercel experience; Python for the data work |
| 2026-11-23 | Backend on Hugging Face Spaces (Docker) | Free tier with enough RAM for pandas; Render free tier is 512 MB |
| 2026-11-23 | Gemini primary, Groq fallback, behind one client | Free tiers; failover against rate limits and model deprecations |
| 2026-11-23 | Temporary sessions, no accounts | Fits free hosting with non-persistent disk; simpler demo |
| 2026-11-23 | LLM sees profiles, never raw rows | Privacy (free-tier data use), token limits, accuracy |
