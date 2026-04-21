from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path

DEFAULT_ITCH_IO_FEEDS = [
    "https://itch.io/feed/new.xml",
    "https://itch.io/feed/featured.xml",
    "https://itch.io/feed/sales.xml",
    "https://itch.io/games/price-free.xml",
]

DEFAULT_WATCHLIST = [
    "brainrot meme",
    "chaos meme",
    "alignment chart",
    "which one are you",
    "tier list meme",
    "character archetype",
    "fandom quiz",
    "which character are you",
    "team picker",
    "alignment test",
    "cozy game",
    "puzzle game",
    "merge game",
    "idle game",
    "wholesome game",
]

DEFAULT_TRENDS_TOPIC_MAP = [
    {
        "topic_key": "brainrot_meme",
        "topic_label": "Brainrot Meme",
        "queries": [
            "brainrot meme",
            "brainrot quiz",
            "brainrot character test",
            "brainrot personality test",
            "chaotic meme quiz",
        ],
    },
    {
        "topic_key": "chaos_identity",
        "topic_label": "Chaos Identity",
        "queries": [
            "chaos meme",
            "alignment chart",
            "which one are you",
            "tier list meme",
            "alignment chart quiz",
            "which chaos type are you",
        ],
    },
    {
        "topic_key": "character_archetype",
        "topic_label": "Character Archetype",
        "queries": [
            "character archetype",
            "character archetype quiz",
            "which character are you",
            "fandom quiz",
            "team picker",
            "alignment test",
            "character personality quiz",
            "what character type are you",
            "which fandom character are you",
        ],
    },
    {
        "topic_key": "cozy_puzzle",
        "topic_label": "Cozy Puzzle",
        "queries": [
            "cozy game",
            "cozy puzzle game",
            "wholesome game",
            "relaxing puzzle game",
            "cozy mystery game",
            "cozy visual novel",
            "wholesome puzzle game",
        ],
    },
    {
        "topic_key": "merge_idle",
        "topic_label": "Merge Idle",
        "queries": [
            "merge game",
            "idle game",
            "merge idle game",
            "merge puzzle game",
            "idle merge game",
            "incremental merge game",
        ],
    },
]


@dataclass(slots=True)
class AppConfig:
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parents[2])
    output_dir: Path = field(init=False)
    database_path: Path = field(init=False)
    default_report_limit: int = 0
    default_rss_feeds: list[str] = field(default_factory=list)
    default_trends_bridge: str | None = None
    default_keywords: list[str] = field(default_factory=list)
    default_trends_topic_map: list[dict] = field(default_factory=list)
    default_trends_output_path: Path = field(init=False)
    default_trends_geo: str = "US"
    default_trends_language: str = "en-US"
    default_trends_timezone: int = 0
    default_trends_timeframe: str = "now 7-d"

    def __post_init__(self) -> None:
        output_dir_override = os.getenv("TREND_PLAY_RADAR_OUTPUT_DIR", "")
        self.output_dir = Path(output_dir_override).expanduser() if output_dir_override else self.project_root / "output"
        database_path_override = os.getenv("TREND_PLAY_RADAR_DATABASE_PATH", "")
        self.database_path = (
            Path(database_path_override).expanduser() if database_path_override else self.output_dir / "trend_play_radar.db"
        )
        self.default_trends_output_path = self.output_dir / "google_trends_bridge.json"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        feeds_value = os.getenv("TREND_PLAY_RADAR_RSS_FEEDS", "")
        self.default_rss_feeds = [item.strip() for item in feeds_value.split(",") if item.strip()] or list(
            DEFAULT_ITCH_IO_FEEDS
        )
        self.default_trends_bridge = os.getenv("TREND_PLAY_RADAR_TRENDS_BRIDGE") or None
        keywords_value = os.getenv("TREND_PLAY_RADAR_KEYWORDS", "")
        self.default_keywords = [item.strip() for item in keywords_value.split(",") if item.strip()] or list(
            DEFAULT_WATCHLIST
        )
        self.default_trends_topic_map = build_default_trends_topic_map(self.default_keywords)
        self.default_trends_geo = os.getenv("TREND_PLAY_RADAR_TRENDS_GEO", self.default_trends_geo)
        self.default_trends_language = os.getenv(
            "TREND_PLAY_RADAR_TRENDS_LANGUAGE", self.default_trends_language
        )
        self.default_trends_timezone = int(
            os.getenv("TREND_PLAY_RADAR_TRENDS_TIMEZONE", str(self.default_trends_timezone))
        )
        self.default_trends_timeframe = os.getenv(
            "TREND_PLAY_RADAR_TRENDS_TIMEFRAME", self.default_trends_timeframe
        )


def get_config() -> AppConfig:
    return AppConfig()


def build_default_trends_topic_map(keywords: list[str]) -> list[dict]:
    if keywords and keywords != DEFAULT_WATCHLIST:
        return [
            {
                "topic_key": slugify_topic(keyword),
                "topic_label": keyword.title(),
                "queries": [keyword],
            }
            for keyword in keywords
        ]
    return [dict(topic) for topic in DEFAULT_TRENDS_TOPIC_MAP]


def slugify_topic(value: str) -> str:
    return value.strip().lower().replace(" ", "_")
