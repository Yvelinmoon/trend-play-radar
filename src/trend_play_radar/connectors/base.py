from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from trend_play_radar.models import RawSignal


@dataclass(slots=True)
class ConnectorContext:
    project_root: Path
    json_input: Path | None = None
    keywords: list[str] = field(default_factory=list)
    rss_feeds: list[str] = field(default_factory=list)
    trends_bridge: str | None = None
    youtube_api_key: str = ""
    youtube_region: str = "US"
    youtube_max_results: int = 25
    youtube_categories: list[str] = field(default_factory=list)


class Connector:
    name = "base"

    def __init__(self, context: ConnectorContext) -> None:
        self.context = context

    def fetch(self) -> list[RawSignal]:
        raise NotImplementedError
