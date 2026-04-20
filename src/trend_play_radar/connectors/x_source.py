from __future__ import annotations

from trend_play_radar.connectors.base import Connector


class XConnector(Connector):
    name = "x"

    def fetch(self) -> list:
        return []
