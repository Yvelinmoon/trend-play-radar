from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from http.client import RemoteDisconnected
from pathlib import Path
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


GOOGLE_TRENDS_ROOT = "https://trends.google.com/trends/api"


class GoogleTrendsBridgeError(RuntimeError):
    pass


@dataclass(slots=True)
class TrendsBridgeOptions:
    queries: list["TrendsQuery"]
    output_path: Path
    geo: str = "US"
    language: str = "en-US"
    timezone_offset: int = 0
    timeframe: str = "now 7-d"


@dataclass(slots=True)
class TrendsQuery:
    topic_key: str
    topic_label: str
    query: str
    tags: list[str]


def build_bridge(options: TrendsBridgeOptions) -> list[dict]:
    records: list[dict] = []
    for batch in batched(options.queries, size=5):
        widget = fetch_timeseries_widget(
            keywords=[item.query for item in batch],
            geo=options.geo,
            language=options.language,
            timezone_offset=options.timezone_offset,
            timeframe=options.timeframe,
        )
        records.extend(
            fetch_keyword_records(
                widget=widget,
                queries=batch,
                geo=options.geo,
                language=options.language,
                timezone_offset=options.timezone_offset,
            )
        )

    options.output_path.parent.mkdir(parents=True, exist_ok=True)
    options.output_path.write_text(json.dumps(records, ensure_ascii=False, indent=2))
    return records


def batched(items: list[str], *, size: int) -> list[list[str]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def fetch_timeseries_widget(
    *,
    keywords: list[str],
    geo: str,
    language: str,
    timezone_offset: int,
    timeframe: str,
) -> dict:
    req = {
        "comparisonItem": [{"keyword": keyword, "geo": geo, "time": timeframe} for keyword in keywords],
        "category": 0,
        "property": "",
    }
    payload = trends_api_request(
        path="explore",
        language=language,
        timezone_offset=timezone_offset,
        params={"req": json.dumps(req, separators=(",", ":"))},
    )
    widgets = payload["widgets"]
    for widget in widgets:
        if widget.get("id") == "TIMESERIES":
            return widget
    raise RuntimeError("Google Trends explore response did not include a TIMESERIES widget")


def fetch_keyword_records(
    *,
    widget: dict,
    queries: list[TrendsQuery],
    geo: str,
    language: str,
    timezone_offset: int,
) -> list[dict]:
    payload = trends_api_request(
        path="widgetdata/multiline",
        language=language,
        timezone_offset=timezone_offset,
        params={
            "req": json.dumps(widget["request"], separators=(",", ":")),
            "token": widget["token"],
        },
    )
    timeline = payload.get("default", {}).get("timelineData", [])
    now = datetime.now(tz=timezone.utc).isoformat()
    records: list[dict] = []
    for index, trend_query in enumerate(queries):
        series = extract_series(timeline, keyword_index=index)
        latest_score = series[-1]["value"] if series else 0
        peak_score = max((point["value"] for point in series), default=0)
        average_score = round(sum(point["value"] for point in series) / len(series), 2) if series else 0.0
        records.append(
            {
                "keyword": trend_query.query,
                "query": trend_query.query,
                "parent_topic": trend_query.topic_key,
                "topic_label": trend_query.topic_label,
                "title": f"Google Trends signal for {trend_query.query}",
                "url": build_explore_url(keyword=trend_query.query, geo=geo),
                "published_at": now,
                "trend_score": latest_score,
                "tags": trend_query.tags,
                "summary": (
                    f"Latest score {latest_score}, peak score {peak_score}, "
                    f"average score {average_score} over {len(series)} samples."
                ),
                "raw_payload": {
                    "topic_key": trend_query.topic_key,
                    "topic_label": trend_query.topic_label,
                    "query": trend_query.query,
                    "geo": geo,
                    "series": series,
                    "peak_score": peak_score,
                    "average_score": average_score,
                },
            }
        )
    return records


def extract_series(timeline: list[dict], *, keyword_index: int) -> list[dict]:
    series: list[dict] = []
    for point in timeline:
        values = point.get("value", [])
        if keyword_index >= len(values):
            continue
        series.append(
            {
                "time": point.get("time"),
                "formatted_time": point.get("formattedTime", ""),
                "value": values[keyword_index],
            }
        )
    return series


def trends_api_request(
    *,
    path: str,
    language: str,
    timezone_offset: int,
    params: dict[str, str],
) -> dict:
    query = {
        "hl": language,
        "tz": str(timezone_offset),
        **params,
    }
    url = f"{GOOGLE_TRENDS_ROOT}/{path}?{urlencode(query)}"
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) trend-play-radar/0.1",
            "Accept": "application/json,text/plain,*/*",
        },
    )
    try:
        with urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        if exc.code == 429:
            raise GoogleTrendsBridgeError(
                "Google Trends returned HTTP 429 (rate limited). "
                "Retry later, use a different network, or point the project at an external bridge JSON."
            ) from exc
        raise GoogleTrendsBridgeError(f"Google Trends request failed with HTTP {exc.code}") from exc
    except RemoteDisconnected as exc:
        raise GoogleTrendsBridgeError(
            "Google Trends closed the connection unexpectedly. "
            "This usually means the request was blocked or throttled."
        ) from exc
    except URLError as exc:
        raise GoogleTrendsBridgeError(f"Google Trends request failed: {exc.reason}") from exc
    return parse_trends_json(raw)


def parse_trends_json(raw: str) -> dict:
    cleaned = raw.lstrip(")]}',\n ")
    return json.loads(cleaned)


def build_explore_url(*, keyword: str, geo: str) -> str:
    query = urlencode({"q": keyword, "geo": geo, "date": "now 7-d"})
    return f"https://trends.google.com/trends/explore?{query}"
