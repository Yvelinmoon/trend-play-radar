from __future__ import annotations

from trend_play_radar.connectors.base import Connector


class TikTokConnector(Connector):
    name = "tiktok"

    def fetch(self) -> list:
        return []
