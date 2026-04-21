from __future__ import annotations

from trend_play_radar.connectors import CONNECTOR_REGISTRY
from trend_play_radar.connectors.base import ConnectorContext
from trend_play_radar.models import RawSignal


def collect_signals(
    connector_names: list[str],
    *,
    project_root,
    json_input=None,
    keywords: list[str] | None = None,
    rss_feeds: list[str] | None = None,
    trends_bridge: str | None = None,
    youtube_api_key: str = "",
    youtube_region: str = "US",
    youtube_max_results: int = 25,
    youtube_categories: list[str] | None = None,
) -> list[RawSignal]:
    context = ConnectorContext(
        project_root=project_root,
        json_input=json_input,
        keywords=keywords or [],
        rss_feeds=rss_feeds or [],
        trends_bridge=trends_bridge,
        youtube_api_key=youtube_api_key,
        youtube_region=youtube_region,
        youtube_max_results=youtube_max_results,
        youtube_categories=youtube_categories or [],
    )
    signals: list[RawSignal] = []

    for name in connector_names:
        connector_cls = CONNECTOR_REGISTRY.get(name)
        if connector_cls is None:
            raise ValueError(f"Unknown connector: {name}")
        connector = connector_cls(context)
        signals.extend(connector.fetch())

    return dedupe_signals(signals)


def dedupe_signals(signals: list[RawSignal]) -> list[RawSignal]:
    seen: set[tuple[str, str]] = set()
    output: list[RawSignal] = []
    for signal in signals:
        key = (signal.platform, signal.external_id)
        if key in seen:
            continue
        seen.add(key)
        output.append(signal)
    return output
