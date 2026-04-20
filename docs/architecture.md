# Architecture

## Product intent

The system exists to answer one question every day:

`Which emerging trends are most worth turning into a lightweight game or interactive within a two-week cycle?`

In the accuracy-first MVP, that question is narrowed further:

`Which topics show enough evidence of real warming to justify making a lightweight playable test?`

## MVP boundaries

Included in this version:

- connector interface for platform fetchers
- shared raw signal schema
- local persistence in SQLite
- deterministic topic clustering
- historical window comparisons
- scoring for trend confidence and execution fit
- auditable evidence in reports
- Markdown and JSON report generation

Explicitly excluded from this version:

- live platform auth and scraping logic
- dashboard UI
- LLM summarization
- scheduling and orchestration
- API server

## Pipeline

```text
connectors -> raw signals -> normalize -> cluster -> baseline comparison -> confidence/execution scoring -> report
```

## Core entities

### RawSignal

Normalized per-post or per-trend input from any source.

Key fields:

- `platform`
- `external_id`
- `title`
- `summary`
- `published_at`
- `engagement`
- `tags`
- `keyword_hint`
- `metrics`

### Topic

A merged trend candidate produced from one or more raw signals.

Key outputs:

- `label`
- `platforms`
- `keywords`
- `current_window_count`
- `baseline_window_average`
- `confidence_score`
- `execution_fit_score`
- `final_priority_score`
- `classification`
- `spike_risk`
- `suggested_game_formats`
- `suggested_marketing_hooks`

## Scoring model

The current score is additive and transparent. It is designed to be auditable.

Dimensions:

- Confidence side:
  - `burst_score`
  - `growth_score`
  - `spread_score`
  - `confirmation_score`
- Execution side:
  - `game_fit_score`
  - `marketing_fit_score`
  - `production_feasibility_score`

The system intentionally separates:

- `confidence_score`: how likely the topic is a real trend rather than a local spike
- `execution_fit_score`: how suitable the topic is for a lightweight game or interactive

This prevents a topic from ranking highly just because it is easy to build.

The final ranking uses:

`final_priority_score = confidence_score * 0.6 + execution_fit_score * 0.4`

## Planned evolution

### Phase 1

Replace scaffold connectors with real integrations:

- Reddit via `PRAW`
- Google Trends via `g-trends` wrapper or service bridge

These two are the first priority because they give the cleanest combination of community discussion plus external demand validation.

### Phase 2

Improve topic quality:

- synonym dictionaries
- keyword watchlists
- embeddings or LLM-assisted topic merge
- lifecycle classification
- spike vs warming heuristics trained from validation feedback

### Phase 3

Expose the system to agents:

- FastAPI endpoints
- natural language query layer
- daily scheduled report generation
- marketing angle and game concept synthesis
