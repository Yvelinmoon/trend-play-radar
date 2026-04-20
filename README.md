# Trend Play Radar

Trend Play Radar is an agent-friendly MVP for finding social trends that can be turned into lightweight game or interactive concepts within a two-week cycle.

This version is accuracy-first. It is optimized to answer:

`Is this topic truly warming up, or is it just a local spike?`

This first version is intentionally simple:

- zero third-party Python dependencies
- local SQLite storage
- pluggable connector interface
- deterministic clustering and scoring
- Markdown and JSON report output
- auditable confidence vs execution-fit scoring

## What it does

The pipeline turns raw platform signals into ranked trend topics:

1. collect raw signals from connectors
2. normalize fields into a shared schema
3. group similar signals into topics
4. compare current activity against previous and baseline windows
5. split judgment into `confidence` and `execution fit`
6. generate a daily report for agent or human review

## Current connectors

- `mock`: sample data for end-to-end local runs
- `json`: load signals from a local JSON file
- `reddit`: scaffold for future PRAW integration
- `tiktok`: scaffold for future TikTok-Api integration
- `x`: scaffold for future twscrape integration
- `google_trends`: scaffold for future validation data

The scaffold connectors return no data by default until credentials and fetch logic are added.

## Quick start

```bash
cd /Users/yves/trend-play-radar
PYTHONPATH=src python3 -m trend_play_radar run --connectors mock
```

Outputs are written to `output/`:

- `latest_report.md`
- `latest_report.json`
- `trend_play_radar.db`

## What the scores mean

Each topic carries two separate judgments:

- `confidence_score`: how likely the topic is a real warming trend rather than a local spike
- `execution_fit_score`: how suitable it is for a two-week lightweight playable or interaction

The report also exposes the evidence used to reach that judgment:

- current 24h vs previous 24h signal counts
- prior baseline average
- platform spread
- spike risk
- explanation lines for manual review

## Useful commands

```bash
PYTHONPATH=src python3 -m trend_play_radar collect --connectors mock
PYTHONPATH=src python3 -m trend_play_radar analyze
PYTHONPATH=src python3 -m trend_play_radar report --limit 5
PYTHONPATH=src python3 -m trend_play_radar run --connectors mock,json --json-input data/sample_signals.json
```

## Project layout

```text
src/trend_play_radar/
  cli.py
  config.py
  models.py
  storage.py
  connectors/
  pipeline/
data/
  sample_signals.json
```

## Roadmap

1. add real connector implementations for Reddit and Google Trends first
2. harden historical baselines and topic snapshots across repeated runs
3. add keyword watchlists and scheduled jobs
4. add LLM summarization and marketing angle suggestions
5. expose the pipeline over FastAPI for agent queries
