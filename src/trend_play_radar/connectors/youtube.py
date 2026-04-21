from __future__ import annotations

import json
import math
import subprocess
from datetime import datetime, timezone
from http.client import IncompleteRead
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from trend_play_radar.connectors.base import Connector
from trend_play_radar.models import RawSignal


YOUTUBE_VIDEOS_API = "https://www.googleapis.com/youtube/v3/videos"
DEFAULT_USER_AGENT = "trend-play-radar/0.1"
MAX_RETRIES = 3


class YouTubeConnector(Connector):
    name = "youtube"

    def fetch(self) -> list[RawSignal]:
        if not self.context.youtube_api_key:
            return []

        signals: list[RawSignal] = []
        categories = self.context.youtube_categories or ["20", "24"]
        for category in categories:
            payload = request_youtube_videos(
                api_key=self.context.youtube_api_key,
                region=self.context.youtube_region,
                max_results=self.context.youtube_max_results,
                category=category,
            )
            signals.extend(build_signals(payload, region=self.context.youtube_region, category=category))
        return dedupe_signals(signals)


def request_youtube_videos(*, api_key: str, region: str, max_results: int, category: str) -> dict:
    query = {
        "part": "snippet,statistics",
        "chart": "mostPopular",
        "regionCode": region,
        "maxResults": str(max(1, min(max_results, 50))),
        "key": api_key,
    }
    if category and category != "0":
        query["videoCategoryId"] = category
    url = f"{YOUTUBE_VIDEOS_API}?{urlencode(query)}"
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": DEFAULT_USER_AGENT,
        },
    )
    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urlopen(request, timeout=20) as response:
                try:
                    raw = response.read()
                except IncompleteRead as exc:
                    raw = exc.partial
            return json.loads(raw.decode("utf-8"))
        except (IncompleteRead, json.JSONDecodeError, URLError) as exc:
            last_error = exc
        except HTTPError:
            raise

        if attempt < MAX_RETRIES:
            sleep(1.0 * attempt)

    try:
        completed = subprocess.run(
            ["curl", "-sS", "--fail", "--compressed", url],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(completed.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        last_error = exc

    assert last_error is not None
    raise last_error


def build_signals(payload: dict, *, region: str, category: str) -> list[RawSignal]:
    output: list[RawSignal] = []
    for item in payload.get("items", []):
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        video_id = item.get("id", "")
        if not video_id:
            continue

        published_at = parse_published_at(snippet.get("publishedAt"))
        title = str(snippet.get("title", "")).strip() or "Untitled YouTube video"
        description = str(snippet.get("description", "")).strip()
        tags = [str(tag).strip().lower() for tag in snippet.get("tags", []) if str(tag).strip()]
        channel_title = str(snippet.get("channelTitle", "")).strip()
        view_count = int(statistics.get("viewCount", 0) or 0)
        like_count = int(statistics.get("likeCount", 0) or 0)
        comment_count = int(statistics.get("commentCount", 0) or 0)

        output.append(
            RawSignal(
                platform="youtube",
                external_id=f"youtube-{video_id}",
                title=title,
                url=f"https://www.youtube.com/watch?v={video_id}",
                published_at=published_at,
                engagement=compute_engagement_score(
                    view_count=view_count,
                    like_count=like_count,
                    comment_count=comment_count,
                ),
                summary=description[:400],
                tags=tags[:12],
                metrics={
                    "view_count": float(view_count),
                    "like_count": float(like_count),
                    "comment_count": float(comment_count),
                },
                author=channel_title,
                keyword_hint=" ".join(part for part in [title, " ".join(tags), channel_title] if part),
                raw_payload={
                    "video_id": video_id,
                    "region": region,
                    "category": category,
                    "channel_title": channel_title,
                    "published_at": published_at.isoformat(),
                },
            )
        )
    return output


def compute_engagement_score(*, view_count: int, like_count: int, comment_count: int) -> float:
    score = math.log10(view_count + 1) * 10.0
    score += math.log10(like_count + 1) * 4.0
    score += math.log10(comment_count + 1) * 3.0
    return round(min(score, 100.0), 1)


def parse_published_at(value: str | None) -> datetime:
    if not value:
        return datetime.now(tz=timezone.utc)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def dedupe_signals(signals: list[RawSignal]) -> list[RawSignal]:
    seen: set[str] = set()
    output: list[RawSignal] = []
    for signal in signals:
        if signal.external_id in seen:
            continue
        seen.add(signal.external_id)
        output.append(signal)
    return output
