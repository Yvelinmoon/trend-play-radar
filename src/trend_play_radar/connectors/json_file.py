from __future__ import annotations

import json
from datetime import datetime

from trend_play_radar.connectors.base import Connector
from trend_play_radar.models import RawSignal


class JsonFileConnector(Connector):
    name = "json"

    def fetch(self) -> list[RawSignal]:
        if self.context.json_input is None:
            return []

        payload = json.loads(self.context.json_input.read_text())
        signals: list[RawSignal] = []
        for item in payload:
            signals.append(
                RawSignal(
                    platform=item["platform"],
                    external_id=item["external_id"],
                    title=item["title"],
                    summary=item.get("summary", ""),
                    url=item["url"],
                    published_at=datetime.fromisoformat(item["published_at"]),
                    engagement=float(item.get("engagement", 0.0)),
                    tags=list(item.get("tags", [])),
                    metrics=dict(item.get("metrics", {})),
                    author=item.get("author", ""),
                    keyword_hint=item.get("keyword_hint", ""),
                    raw_payload=dict(item.get("raw_payload", {})),
                )
            )
        return signals
