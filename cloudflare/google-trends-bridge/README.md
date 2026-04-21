# Cloudflare Google Trends Bridge

This Worker stores and serves the latest bridge JSON in KV for `trend-play-radar`.

## What it does

- accepts published bridge JSON
- stores the latest successful result in KV
- serves the cached JSON over HTTP
- supports manual publish

## Endpoints

- `GET /`
  - returns the latest cached bridge JSON
- `GET /health`
  - returns status and metadata
- `POST /publish`
  - publishes a new bridge payload immediately
  - requires header `x-bridge-secret: <BRIDGE_SECRET>`
  - body should be a JSON array or `{ "records": [...] }`
- `POST /clear`
  - clears cached production payloads
  - requires header `x-bridge-secret: <BRIDGE_SECRET>`
  - optional body: `{ "targets": ["bridge", "report", "debug", "history"] }`
  - when omitted, all cache targets are cleared

## Required setup

1. Create a KV namespace.
2. Put its binding name in `wrangler.toml` as `BRIDGE_CACHE`.
3. Set the secret:

```bash
npx wrangler secret put BRIDGE_SECRET
```

## Deploy

```bash
cd /Users/yves/trend-play-radar/cloudflare/google-trends-bridge
npx wrangler deploy
```

## Local integration

After deployment, point the Python project at the Worker URL:

```bash
export TREND_PLAY_RADAR_TRENDS_BRIDGE="https://<your-worker-domain>"
```

Then run:

```bash
cd /Users/yves/trend-play-radar
PYTHONPATH=src python3 -m trend_play_radar run --connectors rss,google_trends
```

## Publish a bridge payload

Generate or prepare a bridge JSON file, then publish it:

```bash
cd /Users/yves/trend-play-radar
PYTHONPATH=src python3 -m trend_play_radar publish-trends-bridge \
  --bridge-url https://<your-worker-domain>/publish \
  --bridge-secret <your-secret> \
  --input data/sample_google_trends.json
```

Important:

- `data/sample_google_trends.json` is for local testing only.
- Production publish now rejects sample URLs like `trends.google.com/example/...`.
- Only publish bridge payloads generated from a real Google Trends fetch.

## Clear production cache

If sample data or stale data was published earlier, clear it explicitly:

```bash
curl -X POST https://<your-worker-domain>/clear \
  -H "content-type: application/json" \
  -H "x-bridge-secret: <your-secret>" \
  -d '{"targets":["bridge","report","debug","history"]}'
```
