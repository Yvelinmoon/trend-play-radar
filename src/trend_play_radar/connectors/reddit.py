from __future__ import annotations

from trend_play_radar.connectors.base import Connector


class RedditConnector(Connector):
    name = "reddit"

    def fetch(self) -> list:
        return []
