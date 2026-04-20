from __future__ import annotations

from datetime import timedelta

from trend_play_radar.connectors.base import Connector
from trend_play_radar.models import RawSignal, utcnow


class MockConnector(Connector):
    name = "mock"

    def fetch(self) -> list[RawSignal]:
        now = utcnow()
        return [
            RawSignal(
                platform="reddit",
                external_id="reddit-office-brainrot-old-1",
                title="Why every office meme ends in a coworker alignment chart",
                summary="A smaller earlier thread framed office behavior as a shared personality system.",
                url="https://example.com/reddit/office-brainrot-old-1",
                published_at=now - timedelta(days=3, hours=2),
                engagement=420,
                tags=["meme", "office", "alignment", "personality"],
                keyword_hint="office alignment personality",
                metrics={"upvotes": 350, "comments": 70},
                author="user_old_office",
            ),
            RawSignal(
                platform="reddit",
                external_id="reddit-office-brainrot-1",
                title="Office brainrot memes are turning into character archetypes",
                summary="Users classify coworkers into absurd but relatable office personas.",
                url="https://example.com/reddit/office-brainrot-1",
                published_at=now - timedelta(hours=2),
                engagement=1640,
                tags=["meme", "identity", "office", "character"],
                keyword_hint="office brainrot meme",
                metrics={"upvotes": 1400, "comments": 240},
                author="user_recent_office",
            ),
            RawSignal(
                platform="tiktok",
                external_id="tiktok-office-brainrot-9",
                title="POV: every office has these 5 chaos classes",
                summary="Short skits with exaggerated office roles are driving remixes.",
                url="https://example.com/tiktok/office-brainrot-9",
                published_at=now - timedelta(hours=6),
                engagement=9200,
                tags=["meme", "short-form", "identity", "shareable"],
                keyword_hint="office chaos classes",
                metrics={"likes": 8000, "shares": 900, "comments": 300},
                author="creator_office",
            ),
            RawSignal(
                platform="x",
                external_id="x-morning-routine-3",
                title="Goblin mode morning routine is back with productivity parody",
                summary="Creators parody impossible productivity systems with escalating humor.",
                url="https://example.com/x/goblin-routine-3",
                published_at=now - timedelta(hours=4),
                engagement=2100,
                tags=["humor", "routine", "parody"],
                keyword_hint="goblin routine parody",
                metrics={"likes": 1800, "reposts": 200, "replies": 100},
                author="creator_routine",
            ),
            RawSignal(
                platform="google_trends",
                external_id="gt-office-personality-1",
                title="Searches rise for office personality quiz",
                summary="Search interest confirms the office identity trend is spreading outside one platform.",
                url="https://example.com/google/office-personality-1",
                published_at=now - timedelta(hours=8),
                engagement=74,
                tags=["validation", "quiz", "search"],
                keyword_hint="office personality quiz",
                metrics={"trend_index": 74},
            ),
            RawSignal(
                platform="reddit",
                external_id="reddit-boss-fight-old-1",
                title="Imagine your manager as a tiny stage boss",
                summary="An older thread joked about managers having simple attack patterns.",
                url="https://example.com/reddit/boss-fight-old-1",
                published_at=now - timedelta(days=5, hours=4),
                engagement=240,
                tags=["boss fight", "manager", "parody"],
                keyword_hint="manager boss parody",
                metrics={"upvotes": 210, "comments": 30},
                author="user_old_boss",
            ),
            RawSignal(
                platform="reddit",
                external_id="reddit-petty-boss-fight-2",
                title="Petty boss fight parody posts keep climbing",
                summary="Threads imagine absurd mini boss fights against annoying managers.",
                url="https://example.com/reddit/petty-boss-fight-2",
                published_at=now - timedelta(hours=3),
                engagement=980,
                tags=["boss fight", "parody", "combat"],
                keyword_hint="petty boss fight",
                metrics={"upvotes": 830, "comments": 150},
                author="user_recent_boss",
            ),
            RawSignal(
                platform="tiktok",
                external_id="tiktok-petty-boss-fight-6",
                title="If your manager was a side-scrolling boss",
                summary="Creators animate manager quirks as attack patterns and weak points.",
                url="https://example.com/tiktok/petty-boss-fight-6",
                published_at=now - timedelta(hours=5),
                engagement=7600,
                tags=["boss fight", "side-scroller", "workplace"],
                keyword_hint="manager side scrolling boss",
                metrics={"likes": 7000, "shares": 500, "comments": 100},
                author="creator_boss",
            ),
        ]
