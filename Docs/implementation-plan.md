# Phase-Wise Implementation Plan

AI-Powered Restaurant Recommendation System (Zomato Use Case)

This plan translates [context.md](./context.md) and [architecture.md](./architecture.md) into a sequenced build roadmap. Each phase has clear objectives, tasks, deliverables, acceptance criteria, and dependencies.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Phase Summary](#2-phase-summary)
3. [Dependency Graph](#3-dependency-graph)
4. [Phase 0 — Project Foundation](#phase-0--project-foundation)
5. [Phase 1 — Data Ingestion & Preprocessing](#phase-1--data-ingestion--preprocessing)
6. [Phase 2 — Domain Models & Configuration](#phase-2--domain-models--configuration)
7. [Phase 3 — User Preferences & Filtering](#phase-3--user-preferences--filtering)
8. [Phase 4 — LLM Recommendation Engine](#phase-4--llm-recommendation-engine)
9. [Phase 5 — Integration Orchestrator](#phase-5--integration-orchestrator)
10. [Phase 6 — Presentation & End-to-End UI](#phase-6--presentation--end-to-end-ui)
11. [Phase 7 — Testing, Hardening & Documentation](#phase-7--testing-hardening--documentation)
12. [Phase 8 (Optional) — Demo & Deployment Readiness](#phase-8-optional--demo--deployment-readiness)
13. [Milestone Checklist](#milestone-checklist)
14. [Risk Register](#risk-register)

---

## 1. Overview

### 1.1 End-to-End Pipeline (target state)

```
Ingest → Input → Filter → LLM → Display
```

| Workflow step ([context.md](./context.md)) | Primary modules ([architecture.md](./architecture.md)) |
|--------------------------------------------|----------------------------------------------------------|
| Data Ingestion | `DatasetLoader`, `Preprocessor`, `RestaurantStore` |
| User Input | `PreferenceService`, `PresentationModule` (form) |
| Integration Layer | `FilterEngine`, `PromptBuilder`, `RecommendationOrchestrator` |
| Recommendation Engine | `LLMClient`, `parser` |
| Output Display | `PresentationModule` (results) |

### 1.2 Recommended stack (from architecture)

| Area | Default choice |
|------|----------------|
| Language | Python 3.10+ |
| Data | `datasets`, `pandas` |
| UI | Streamlit |
| LLM | Google Gemini API (`google-generativeai`) |
| Config | `pydantic-settings`, `.env` |

### 1.3 Guiding principles during build

1. Build **bottom-up**: data → filter → LLM → UI.
2. Keep each phase **demoable** before moving on.
3. **Filter first, LLM second** — never send the full dataset to the model.
4. Restaurant **facts always come from the dataset**, not the LLM.

---

## 2. Phase Summary

| Phase | Name | Est. effort | Outcome |
|-------|------|-------------|---------|
| **0** | Project Foundation | 0.5–1 day | Repo, deps, config, folder layout |
| **1** | Data Ingestion & Preprocessing | 1–2 days | Clean `Restaurant` list from Hugging Face |
| **2** | Domain Models & Configuration | 0.5–1 day | Typed models, settings, env template |
| **3** | User Preferences & Filtering | 1–2 days | Valid prefs + deterministic shortlist |
| **4** | LLM Recommendation Engine | 1–2 days | Prompt, client, JSON parse, validation |
| **5** | Integration Orchestrator | 1 day | Full pipeline minus UI |
| **6** | Presentation & E2E UI | 1–2 days | Form + results cards, loading states |
| **7** | Testing, Hardening & Docs | 1–2 days | Tests, README, edge cases, fallbacks |
| **8** *(optional)* | Demo & Deployment | 0.5–1 day | Cache, polish, optional Docker |

**Total (Phases 0–7):** ~7–12 working days for a single developer.

---

## 3. Dependency Graph

```
Phase 0 (Foundation)
    │
    ├──▶ Phase 2 (Models & Config) ──┐
    │                               │
    └──▶ Phase 1 (Data) ────────────┼──▶ Phase 3 (Filter) ──▶ Phase 5 (Orchestrator) ──▶ Phase 6 (UI)
                                    │           │
                                    │           └──▶ Phase 4 (LLM) ──┘
                                    │
                                    └── (models used in Phase 1 loader output)

Phase 6 ──▶ Phase 7 (Testing & Docs)
Phase 7 ──▶ Phase 8 (Optional deploy)
```

**Critical path:** 0 → 1 → 3 → 4 → 5 → 6 → 7

---

## Phase 0 — Project Foundation

**Maps to:** Architecture §11 (stack), §11.1 (layout)  
**Workflow:** Prerequisites for all steps

### Objectives

- Create repository structure and development environment.
- Lock in implementation choices (UI, LLM provider) for the milestone.
- Establish configuration and secrets handling.

### Tasks

| # | Task | Details |
|---|------|---------|
| 0.1 | Initialize project | Create folder layout per architecture §11.1 |
| 0.2 | Dependency management | `requirements.txt` or `pyproject.toml`: `datasets`, `pandas`, `pydantic`, `pydantic-settings`, `streamlit`, `google-generativeai` |
| 0.3 | Environment template | `.env.example` with `LLM_API_KEY` (Gemini key), `LLM_MODEL`, `HF_DATASET_ID`, `MAX_CANDIDATES`, `TOP_K` |
| 0.4 | Settings module | `config/settings.py` loading env with defaults |
| 0.5 | Tooling | `.gitignore` (`.env`, `__pycache__`, `.cache/`, data cache) |
| 0.6 | Decision log | Note chosen UI (Streamlit) and LLM provider (Google Gemini) in README stub |

### Deliverables

- [ ] Runnable empty app entry (`app/main.py` prints or shows placeholder)
- [ ] `requirements.txt` installable via `pip install -r requirements.txt`
- [ ] `.env.example` documented

### Acceptance criteria

- `python -m app.main` or `streamlit run app/main.py` starts without import errors.
- Secrets are not committed; only `.env.example` is in repo.

### Exit gate

Proceed when project installs cleanly on a fresh machine.

---

## Phase 1 — Data Ingestion & Preprocessing

**Maps to:** [context.md](./context.md) § Data Ingestion; Architecture §3.2.1–3.2.2, §4  
**Workflow step:** 1. Data Ingestion

### Objectives

- Load [Zomato dataset on Hugging Face](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation).
- Normalize records into a consistent internal shape ready for filtering.

### Tasks

| # | Task | Details |
|---|------|---------|
| 1.1 | Implement `DatasetLoader` | `datasets.load_dataset("ManikaSaini/zomato-restaurant-recommendation")` |
| 1.2 | Inspect schema | Log column names; document mapping in code comments or config |
| 1.3 | Field mapping | Map to: `id`, `name`, `location`, `cuisines`, `rating`, `cost_for_two`, `budget_band` |
| 1.4 | Implement `Preprocessor` | Trim strings, parse comma-separated cuisines, coerce rating to float |
| 1.5 | Budget bands | Map cost to `low` / `medium` / `high` per architecture §4.4 thresholds |
| 1.6 | Data quality | Drop rows missing name or location; handle `"NEW"` or non-numeric ratings |
| 1.7 | In-memory store | `RestaurantStore` singleton or module-level cache loaded once |
| 1.8 | Optional disk cache | Save preprocessed Parquet/CSV for faster restarts |
| 1.9 | Exploration script | Small script or notebook: print row count, sample cities, cuisine samples |

### Deliverables

- [ ] `app/data/loader.py`
- [ ] `app/data/preprocessor.py`
- [ ] `get_restaurants() -> list[Restaurant]` (or DataFrame) usable by downstream code

### Acceptance criteria

- Dataset loads successfully from Hugging Face (or cached file if offline).
- At least 100+ valid restaurants after cleaning (exact count depends on dataset).
- Sample output shows sensible `name`, `location`, `cuisines`, `rating`, `budget_band`.
- Load time acceptable with cache (&lt; 30s first run; &lt; 5s cached).

### Tests (start in this phase)

- Unit: cuisine split, rating parse, budget band mapping
- Unit: invalid rows dropped

### Exit gate

`python -c "from app.data.loader import load; print(len(load()))"` returns expected count.

---

## Phase 2 — Domain Models & Configuration

**Maps to:** Architecture §4.2, §9.3  
**Can run in parallel with:** Phase 1 (start after Phase 0)

### Objectives

- Define typed domain models shared across all layers.
- Centralize configuration constants.

### Tasks

| # | Task | Details |
|---|------|---------|
| 2.1 | `Restaurant` model | Pydantic/dataclass per architecture §4.2 |
| 2.2 | `UserPreferences` model | location (required), budget, cuisine, min_rating, extras |
| 2.3 | `Recommendation` model | rank, restaurant, explanation |
| 2.4 | `RecommendationResponse` model | list, optional summary, filters_applied, candidate_count |
| 2.5 | Enums | `BudgetBand`: low, medium, high |
| 2.6 | Wire settings | `MAX_CANDIDATES`, `TOP_K`, `BUDGET_THRESHOLDS` in settings |

### Deliverables

- [ ] `app/models.py`
- [ ] Updated `config/settings.py` with all keys

### Acceptance criteria

- Models serialize/deserialize to JSON for LLM prompts.
- Invalid budget values rejected at validation time.

### Exit gate

Import models from any module without circular imports.

---

## Phase 3 — User Preferences & Filtering

**Maps to:** [context.md](./context.md) § User Input, § Integration Layer (filter half); Architecture §3.2.3–3.2.4, §6  
**Workflow steps:** 2. User Input (validation); 3. Integration Layer (filtering)

### Objectives

- Validate and normalize user preferences.
- Produce a deterministic, rating-sorted shortlist capped at N candidates.

### Tasks

| # | Task | Details |
|---|------|---------|
| 3.1 | `PreferenceService` | `from_raw(dict) -> UserPreferences` with validation errors |
| 3.2 | Location normalization | Case-insensitive match; optional city list from dataset for dropdown later |
| 3.3 | Cuisine normalization | Strip, title-case; support partial match |
| 3.4 | Implement `FilterEngine` | AND filters: location, budget, cuisine, min_rating |
| 3.5 | Extras handling | Pass `extras` through to prefs object; no hard filter unless dataset supports field |
| 3.6 | Sort & cap | Sort by rating DESC; take first `MAX_CANDIDATES` (default 30) |
| 3.7 | Empty-result helper | Return structured empty response with message (no LLM call) |
| 3.8 | CLI smoke test | Script: accept args, print filter count and top 5 names |

### Deliverables

- [ ] `app/services/preferences.py`
- [ ] `app/services/filter.py`
- [ ] CLI or test proving filter works on real data

### Acceptance criteria

| Test case | Expected |
|-----------|----------|
| Location = "Bangalore" | Only Bangalore restaurants |
| budget = low | Only `budget_band == low` |
| cuisine = Italian | Restaurants with Italian in cuisines |
| min_rating = 4.0 | rating ≥ 4.0 |
| Impossible combo | Empty list + clear message |
| Broad query | List capped at N, sorted by rating |

### Tests

- Unit: each filter in isolation
- Unit: combined filters + cap behavior
- Unit: preference validation errors

### Exit gate

Filter returns correct shortlist for 3+ manual test queries against live data.

---

## Phase 4 — LLM Recommendation Engine

**Maps to:** [context.md](./context.md) § Recommendation Engine; Architecture §7  
**Workflow step:** 4. Recommendation Engine (LLM)  
**Provider:** Google Gemini via `google-generativeai` SDK

### Objectives

- Rank and explain restaurants via Gemini using only the candidate shortlist.
- Parse structured JSON and guard against hallucinations.

### Tasks

| # | Task | Details |
|---|------|---------|
| 4.1 | `PromptBuilder` | System + user messages; embed prefs + candidate JSON |
| 4.2 | Prompt rules | Only use provided IDs; output schema; mention user prefs in explanations |
| 4.3 | `LLMClient` | Gemini adapter (`google-generativeai`) with timeout, retries, configurable model/temperature |
| 4.4 | Output schema | JSON: `summary`, `recommendations[{id, rank, explanation}]` |
| 4.5 | `parser.py` | Parse JSON; handle markdown fences; retry on malformed JSON |
| 4.6 | Validation | Every `id` must exist in candidate set; drop unknowns |
| 4.7 | Field merge | Overlay name, cuisine, rating, cost from dataset onto LLM ranks |
| 4.8 | Fallback mode | On LLM failure: top-K by rating + template explanation |
| 4.9 | Mock client | `MockLLMClient` returning fixed JSON for tests |
| 4.10 | Prompt iteration | Test 3–5 preference combos; tune temperature (0.2–0.5) |

### Deliverables

- [ ] `app/llm/prompts.py`
- [ ] `app/llm/client.py`
- [ ] `app/llm/parser.py`
- [ ] `get_llm_recommendations(prefs, candidates) -> list[Recommendation]`

### Acceptance criteria

- LLM returns top K (default 5) ranked items with explanations (via Gemini).
- No recommended restaurant ID outside candidate list.
- Explanations reference location, budget, cuisine, or rating where relevant.
- Fallback triggers when API key missing or request fails (configurable strict mode for dev).

### Tests

- Contract: parser handles valid/invalid JSON
- Integration: mock LLM → validated `Recommendation` list
- Manual: real API call with small candidate set

### Exit gate

Standalone script: filter → LLM → print 5 recommendations with explanations.

---

## Phase 5 — Integration Orchestrator

**Maps to:** Architecture §3.2.7, §5, §6; [context.md](./context.md) § Integration Layer (full)  
**Workflow step:** 3. Integration Layer (orchestration)

### Objectives

- Wire all backend components into a single `get_recommendations()` API.
- Enforce pipeline rules: empty candidates skip LLM; facts from dataset only.

### Tasks

| # | Task | Details |
|---|------|---------|
| 5.1 | `RecommendationOrchestrator` | Single entry: `get_recommendations(prefs) -> RecommendationResponse` |
| 5.2 | Pipeline steps | load store → filter → build prompt → LLM → parse → merge → build response |
| 5.3 | Metadata | Populate `filters_applied`, `candidate_count` |
| 5.4 | Logging | INFO: candidate count, latency; WARN: dropped hallucinated IDs |
| 5.5 | Error handling | Wrap LLM/dataset errors into user-safe messages |
| 5.6 | Top-K trim | Return at most `TOP_K` after LLM rank |
| 5.7 | Integration test | End-to-end with `MockLLMClient` |

### Deliverables

- [ ] `app/services/orchestrator.py`
- [ ] Public API documented in docstring

### Acceptance criteria

```text
get_recommendations(valid_prefs) → RecommendationResponse with ≤ TOP_K items
get_recommendations(impossible_prefs) → empty recommendations + message, no LLM call
```

- Orchestrator completes in &lt; 20s with real LLM (typical).
- Response objects ready for UI rendering without extra transformation.

### Exit gate

CLI command runs full pipeline: input prefs JSON → stdout JSON response.

---

## Phase 6 — Presentation & End-to-End UI

**Maps to:** [context.md](./context.md) § User Input, § Output Display; Architecture §8  
**Workflow steps:** 2. User Input (UI); 5. Output Display

### Objectives

- Collect preferences via a user-friendly interface.
- Display recommendations with all required fields and AI explanations.

### Tasks

| # | Task | Details |
|---|------|---------|
| 6.1 | Streamlit app shell | Title, description, sidebar or main form |
| 6.2 | Input form | Location (text/select), budget, cuisine, min rating slider, extras text |
| 6.3 | Submit handler | Validate → call orchestrator → handle errors |
| 6.4 | Loading state | Spinner during dataset load (first run) and LLM call |
| 6.5 | Results cards | Per item: name, cuisine, rating, cost/budget, rank, explanation |
| 6.6 | Summary block | Optional LLM `summary` at top |
| 6.7 | Empty state | Message when no matches; suggest relaxing filters |
| 6.8 | Error state | API key missing, network error, with retry guidance |
| 6.9 | City dropdown (optional) | Populate location select from distinct dataset cities |
| 6.10 | UX polish | Spacing, headers, divider between cards |

### Deliverables

- [ ] `app/main.py` (Streamlit entry)
- [ ] Runnable demo: `streamlit run app/main.py`

### Acceptance criteria (maps to [context.md](./context.md) success criteria)

| Criterion | Verified by |
|-----------|-------------|
| Recommendations reflect prefs | Manual test: Delhi + Italian + medium budget |
| LLM explains why | Each card shows explanation text |
| Easy to scan | Fixed field order on every card |
| End-to-end pipeline | Single button from form to results |

### Exit gate

Non-technical user can complete a full recommendation flow in the UI.

---

## Phase 7 — Testing, Hardening & Documentation

**Maps to:** Architecture §10; [context.md](./context.md) success criteria (verification)  
**Workflow:** Quality gate for milestone delivery

### Objectives

- Automated tests for critical paths.
- Resilience, logging, and complete project documentation.

### Tasks

| # | Task | Details |
|---|------|---------|
| 7.1 | Unit tests | Preprocessor, budget mapping, filter, preference validation |
| 7.2 | Integration tests | Orchestrator + mock LLM |
| 7.3 | Contract tests | LLM JSON parser edge cases |
| 7.4 | E2E test | Optional: Streamlit session script or API-level E2E |
| 7.5 | Edge cases | Empty filter, LLM timeout, malformed JSON, single candidate |
| 7.6 | Security pass | No keys in repo; `.env` in `.gitignore` |
| 7.7 | README | Install, env setup, run commands, architecture link |
| 7.8 | Demo script | Document 2–3 example queries for evaluators |
| 7.9 | Code cleanup | Remove debug prints; consistent logging |
| 7.10 | Final review | Trace each success criterion to a test or demo step |

### Deliverables

- [ ] `tests/` with passing `pytest` (or unittest) suite
- [ ] Complete `README.md`
- [ ] Demo query examples in README

### Acceptance criteria

- All tests pass locally.
- README allows new developer to run app in &lt; 15 minutes.
- All four [context.md](./context.md) success criteria demonstrated and documented.

### Exit gate

**Milestone complete** — ready for submission/demo.

---

## Phase 8 (Optional) — Demo & Deployment Readiness

**Maps to:** Architecture §12  
**Out of scope for minimum milestone** — use if time permits

### Objectives

- Faster repeat demos and optional packaging for sharing.

### Tasks

| # | Task | Details |
|---|------|---------|
| 8.1 | Dataset cache | Commit or download script for preprocessed Parquet |
| 8.2 | LLM response cache | Hash(prefs + candidate_ids) for repeated demos |
| 8.3 | Dockerfile | Optional container with env injection |
| 8.4 | Streamlit Cloud / HF Spaces | Deploy public demo (secrets via platform) |
| 8.5 | Performance | Warm load on startup; log timing metrics |

### Deliverables

- [ ] Optional Dockerfile or deploy config
- [ ] One-page DEPLOY.md

### Acceptance criteria

- Cold start demo &lt; 10s when cache warm.
- Deployed URL works for evaluator (if required).

---

## Milestone Checklist

Use this as a final go/no-go list before submission.

### Functional

- [ ] Loads Zomato data from Hugging Face
- [ ] Accepts: location, budget, cuisine, min rating, extras
- [ ] Filters restaurants deterministically
- [ ] LLM ranks and explains (not inventing restaurants)
- [ ] UI shows: name, cuisine, rating, cost, explanation
- [ ] Empty and error states handled gracefully

### Non-functional

- [ ] API keys via environment only
- [ ] LLM fallback or clear error when unavailable
- [ ] README with setup and run instructions
- [ ] Tests for filter and parser (minimum)

### Documentation

- [ ] [context.md](./context.md) requirements met
- [ ] Implementation aligns with [architecture.md](./architecture.md)
- [ ] This plan’s phases 0–7 completed

---

## Risk Register

| Risk | Impact | Mitigation | Phase |
|------|--------|------------|-------|
| Hugging Face dataset schema differs from docs | Load/preprocess breaks | Inspect columns on day 1; configurable field map | 1 |
| HF download slow/unavailable | Blocked development | Disk cache; sample CSV fallback for tests | 1, 7 |
| LLM invents restaurants | Wrong recommendations | ID whitelist validation in parser | 4, 5 |
| LLM returns invalid JSON | Pipeline crash | Parser retry + fallback ranking | 4, 5 |
| High API cost/latency | Slow or expensive demos | Cap candidates (30); use smaller model | 3, 4 |
| Location strings inconsistent | Empty filters | Normalize cities; dropdown from data | 1, 6 |
| “Extras” not in dataset | Feature appears ignored | Document as soft signal in LLM prompt only | 3, 4 |
| No API key for evaluators | Demo fails | Mock mode + README instructions (Gemini key from Google AI Studio) | 0, 7 |

---

## Suggested Weekly Schedule (example)

| Week | Phases | Focus |
|------|--------|-------|
| **Week 1** | 0, 1, 2, 3 | Data pipeline + filtering working in CLI |
| **Week 2** | 4, 5, 6 | LLM + orchestrator + Streamlit UI |
| **Week 3** | 7, 8 | Tests, README, polish, optional deploy |

---

## Task-to-Component Traceability

| Component ([architecture.md](./architecture.md)) | Implemented in phase |
|--------------------------------------------------|----------------------|
| `DatasetLoader` | 1 |
| `Preprocessor` | 1 |
| `Restaurant` / `UserPreferences` / `Recommendation` | 2 |
| `PreferenceService` | 3 |
| `FilterEngine` | 3 |
| `PromptBuilder` | 4 |
| `LLMClient` | 4 |
| `parser` | 4 |
| `RecommendationOrchestrator` | 5 |
| `PresentationModule` | 6 |
| Tests & README | 7 |

---

## Related Documents

| Document | Role |
|----------|------|
| [context.md](./context.md) | Requirements and success criteria |
| [architecture.md](./architecture.md) | System design and module specs |
| [ProblemStatement.txt](./ProblemStatement.txt) | Original assignment |
| `README.md` | Created in Phase 7 — setup and usage |

---

*Generated from architecture.md and context.md — AI-Powered Restaurant Recommendation System (Zomato Use Case).*
