from trend_play_radar.connectors.base import Connector
from trend_play_radar.connectors.google_trends import GoogleTrendsConnector
from trend_play_radar.connectors.json_file import JsonFileConnector
from trend_play_radar.connectors.mock import MockConnector
from trend_play_radar.connectors.reddit import RedditConnector
from trend_play_radar.connectors.rss import RSSConnector
from trend_play_radar.connectors.tiktok import TikTokConnector
from trend_play_radar.connectors.youtube import YouTubeConnector
from trend_play_radar.connectors.x_source import XConnector

CONNECTOR_REGISTRY = {
    "mock": MockConnector,
    "json": JsonFileConnector,
    "rss": RSSConnector,
    "reddit": RedditConnector,
    "tiktok": TikTokConnector,
    "youtube": YouTubeConnector,
    "x": XConnector,
    "google_trends": GoogleTrendsConnector,
}

__all__ = ["CONNECTOR_REGISTRY", "Connector"]
