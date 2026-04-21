from __future__ import annotations

import json
from datetime import datetime, timezone
from trend_play_radar.connectors.base import Connector
from trend_play_radar.connectors.rss import read_resource
from trend_play_radar.models import RawSignal


class GoogleTrendsConnector(Connector):
    name = "google_trends"

    def fetch(self) -> list[RawSignal]:
        if not self.context.trends_bridge:
            return []

        payload = json.loads(read_resource(self.context.trends_bridge).decode("utf-8"))
        signals: list[RawSignal] = []
        for item in payload:
            keyword = item["keyword"].strip()
            topic_label = item.get("topic_label", "").strip()
            title = item.get("title", f"Google Trends signal for {keyword}")
            url = item.get("url", self.context.trends_bridge)
            published_at = parse_published_at(item.get("published_at"))
            trend_score = float(item.get("trend_score", item.get("engagement", 0.0)))
            tags = list(item.get("tags", []))
            signals.append(
                RawSignal(
                    platform="google_trends",
                    external_id=item.get("external_id", f"gt-{keyword.lower().replace(' ', '-')}-{published_at.date()}"),
                    title=title,
                    url=url,
                    published_at=published_at,
                    engagement=trend_score,
                    summary=item.get("summary", ""),
                    tags=tags,
                    metrics={"trend_score": trend_score},
                    author="",
                    keyword_hint=" ".join(part for part in [topic_label, item.get("query", ""), keyword] if part),
                    raw_payload=item,
                )
            )
        return signals


def parse_published_at(value: str | None) -> datetime:
    if not value:
        return datetime.now(tz=timezone.utc)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
