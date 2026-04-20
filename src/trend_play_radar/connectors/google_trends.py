from __future__ import annotations

from trend_play_radar.connectors.base import Connector


class GoogleTrendsConnector(Connector):
    name = "google_trends"

    def fetch(self) -> list:
        return []
