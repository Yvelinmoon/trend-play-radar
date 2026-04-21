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
- `rss`: fetch RSS or Atom feeds automatically
- `youtube`: fetch YouTube `mostPopular` videos through the official Data API
- `google_trends`: load automatic trend-validation data from a bridge URL or file
- `reddit`: scaffold for future PRAW integration
- `tiktok`: scaffold for future TikTok-Api integration
- `x`: scaffold for future twscrape integration

The Reddit, TikTok, and X connectors are still scaffolds. RSS and Google Trends bridge are available now.
YouTube is also available when you provide a YouTube Data API key.

## Quick start

```bash
cd /Users/yves/trend-play-radar
PYTHONPATH=src python3 -m trend_play_radar run --connectors mock
```

With the current project defaults, the first real-source setup is:

- RSS feeds:
  - `https://itch.io/feed/new.xml`
  - `https://itch.io/feed/featured.xml`
  - `https://itch.io/feed/sales.xml`
  - `https://itch.io/games/price-free.xml`
- watchlist:
  - `brainrot meme`
  - `chaos meme`
  - `alignment chart`
  - `which one are you`
  - `tier list meme`
  - `character archetype`
  - `fandom quiz`
  - `which character are you`
  - `team picker`
  - `alignment test`
  - `cozy game`
  - `puzzle game`
  - `merge game`
  - `idle game`
  - `wholesome game`

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
PYTHONPATH=src python3 -m trend_play_radar run --connectors rss,google_trends --rss-feeds data/sample_feed.xml --trends-bridge data/sample_google_trends.json
```

`data/sample_google_trends.json` is a local test fixture. Do not publish it to the production Cloudflare bridge.

## Automatic-source setup

You can run the project without Reddit by using automatic feeds and a Google Trends bridge:

```bash
PYTHONPATH=src python3 -m trend_play_radar run \
  --connectors rss,google_trends \
  --rss-feeds https://example.com/feed.xml,https://example.com/atom.xml \
  --trends-bridge https://example.com/google-trends-bridge.json \
  --keywords "office personality quiz,dating red flag checklist"
```

You can also set defaults with environment variables:

```bash
export TREND_PLAY_RADAR_RSS_FEEDS="https://example.com/feed.xml,https://example.com/atom.xml"
export TREND_PLAY_RADAR_TRENDS_BRIDGE="https://example.com/google-trends-bridge.json"
export TREND_PLAY_RADAR_YOUTUBE_API_KEY="your-youtube-data-api-key"
export TREND_PLAY_RADAR_YOUTUBE_REGION="US"
export TREND_PLAY_RADAR_YOUTUBE_CATEGORIES="20,24"
```

The project also includes a local bridge builder:

```bash
PYTHONPATH=src python3 -m trend_play_radar build-trends-bridge
```

Note: direct Google Trends requests can be rate-limited with HTTP 429 depending on network conditions. When that happens, keep using the same connector contract and point `--trends-bridge` at a JSON file or external bridge endpoint instead.

## Recommended Local Google Flow

If Cloudflare cannot fetch Google Trends reliably, use your local network for Google and publish the result back to the live dashboard:

```bash
export TREND_PLAY_RADAR_BRIDGE_SECRET="your-bridge-secret"
cd /Users/yves/trend-play-radar
PYTHONPATH=src python3 -m trend_play_radar local-google-refresh --fresh
```

What this does in one command:

- fetches Google Trends locally
- collects RSS + local Google bridge data
- rebuilds the report and debug snapshot
- publishes `bridge`, `report`, and `debug-sources` to the Cloudflare Worker

Optional overrides:

```bash
PYTHONPATH=src python3 -m trend_play_radar local-google-refresh \
  --worker-base-url https://<your-worker-domain> \
  --bridge-secret <your-secret> \
  --keywords "brainrot meme,cozy game"
```

## Local YouTube Flow

If you want a more stable broad-audience validation source, use YouTube locally and publish the analyzed result back to the live dashboard:

```bash
export TREND_PLAY_RADAR_BRIDGE_SECRET="your-bridge-secret"
export TREND_PLAY_RADAR_YOUTUBE_API_KEY="your-youtube-data-api-key"
cd /Users/yves/trend-play-radar
PYTHONPATH=src python3 -m trend_play_radar local-youtube-refresh --fresh
```

This command:

- fetches YouTube `mostPopular` videos through the official API
- combines them with RSS signals
- rebuilds the report and debug snapshot
- publishes the live report and debug payload to Cloudflare

You can also run the connector directly in local analysis:

```bash
PYTHONPATH=src python3 -m trend_play_radar run --fresh --connectors rss,youtube
```

For Cloudflare deployment, a ready-to-deploy Worker bridge is included in:

- [cloudflare/google-trends-bridge/README.md](/Users/yves/trend-play-radar/cloudflare/google-trends-bridge/README.md)

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

## Dashboard

A lightweight static dashboard is included at:

- [dashboard/index.html](/Users/yves/trend-play-radar/dashboard/index.html)

Run a local file server from the repo root:

```bash
cd /Users/yves/trend-play-radar
python3 -m http.server 4173
```

Then open:

```text
http://127.0.0.1:4173/dashboard/
```

The dashboard will try to load `/output/latest_report.json` automatically. It also supports loading a report URL or dropping a `latest_report.json` file into the page.

For a Cloudflare Pages deployment, publish the `dashboard/` directory as a static site. The page supports:

- `?report=<url>` query string for a remote JSON report URL
- `?refresh=<seconds>` query string for automatic polling
- remembering the last successful report URL in local storage
- loading a local `latest_report.json` file manually

If you want the deployed dashboard to load the Cloudflare bridge or any other external JSON URL directly in the browser, keep CORS enabled on that endpoint.

To publish the full analyzed report to Cloudflare, use the Worker endpoint:

```bash
PYTHONPATH=src python3 -m trend_play_radar publish-report \
  --report-url https://<your-worker-domain>/publish-report \
  --bridge-secret <your-secret> \
  --input output/latest_report.json
```

Then open the dashboard with:

```text
https://<your-pages-domain>/?report=https://<your-worker-domain>/report&refresh=60
```

## Roadmap

1. add real connector implementations for Reddit and Google Trends first
2. harden historical baselines and topic snapshots across repeated runs
3. add keyword watchlists and scheduled jobs
4. add LLM summarization and marketing angle suggestions
5. expose the pipeline over FastAPI for agent queries
