from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from trend_play_radar.models import RawSignal, Topic


SCHEMA = """
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    external_id TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    published_at TEXT NOT NULL,
    engagement REAL NOT NULL,
    summary TEXT NOT NULL,
    tags_json TEXT NOT NULL,
    metrics_json TEXT NOT NULL,
    author TEXT NOT NULL,
    keyword_hint TEXT NOT NULL,
    raw_payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_key TEXT NOT NULL UNIQUE,
    label TEXT NOT NULL,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS topic_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analyzed_at TEXT NOT NULL,
    topic_key TEXT NOT NULL,
    label TEXT NOT NULL,
    payload_json TEXT NOT NULL
);
"""


class Storage:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.database_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def upsert_signals(self, signals: list[RawSignal]) -> int:
        count = 0
        for signal in signals:
            self.conn.execute(
                """
                INSERT OR REPLACE INTO signals (
                    platform, external_id, title, url, published_at, engagement,
                    summary, tags_json, metrics_json, author, keyword_hint, raw_payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    signal.platform,
                    signal.external_id,
                    signal.title,
                    signal.url,
                    signal.published_at.isoformat(),
                    signal.engagement,
                    signal.summary,
                    json.dumps(signal.tags),
                    json.dumps(signal.metrics),
                    signal.author,
                    signal.keyword_hint,
                    json.dumps(signal.raw_payload),
                ),
            )
            count += 1
        self.conn.commit()
        return count

    def clear_all(self) -> None:
        self.conn.execute("DELETE FROM signals")
        self.conn.execute("DELETE FROM topics")
        self.conn.execute("DELETE FROM topic_snapshots")
        self.conn.commit()

    def load_signals(self) -> list[RawSignal]:
        rows = self.conn.execute("SELECT * FROM signals ORDER BY published_at DESC").fetchall()
        return [
            RawSignal(
                platform=row["platform"],
                external_id=row["external_id"],
                title=row["title"],
                url=row["url"],
                published_at=self._parse_datetime(row["published_at"]),
                engagement=row["engagement"],
                summary=row["summary"],
                tags=json.loads(row["tags_json"]),
                metrics=json.loads(row["metrics_json"]),
                author=row["author"],
                keyword_hint=row["keyword_hint"],
                raw_payload=json.loads(row["raw_payload_json"]),
            )
            for row in rows
        ]

    def replace_topics(self, topics: list[Topic]) -> None:
        from datetime import datetime, timezone

        analyzed_at = datetime.now(tz=timezone.utc).isoformat()
        self.conn.execute("DELETE FROM topics")
        for topic in topics:
            payload = json.dumps(topic.to_record(), ensure_ascii=False, indent=2)
            self.conn.execute(
                "INSERT INTO topics (topic_key, label, payload_json) VALUES (?, ?, ?)",
                (topic.topic_key, topic.label, payload),
            )
            self.conn.execute(
                """
                INSERT INTO topic_snapshots (analyzed_at, topic_key, label, payload_json)
                VALUES (?, ?, ?, ?)
                """,
                (analyzed_at, topic.topic_key, topic.label, payload),
            )
        self.conn.commit()

    def load_topics(self) -> list[dict]:
        rows = self.conn.execute("SELECT payload_json FROM topics ORDER BY id ASC").fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def close(self) -> None:
        self.conn.close()

    @staticmethod
    def _parse_datetime(value: str):
        from datetime import datetime

        return datetime.fromisoformat(value)
