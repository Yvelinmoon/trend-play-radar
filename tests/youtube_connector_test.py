from pathlib import Path
import sys
from unittest import TestCase

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from trend_play_radar.connectors.youtube import build_signals, compute_engagement_score


class YouTubeConnectorTest(TestCase):
    def test_build_signals_from_most_popular_payload(self) -> None:
        payload = {
            "items": [
                {
                    "id": "abc123",
                    "snippet": {
                        "title": "Cozy puzzle build challenge",
                        "description": "A cozy game prototype breakdown",
                        "publishedAt": "2026-04-21T10:00:00Z",
                        "channelTitle": "PlayLab",
                        "tags": ["cozy", "puzzle", "prototype"],
                    },
                    "statistics": {
                        "viewCount": "125000",
                        "likeCount": "9100",
                        "commentCount": "440",
                    },
                }
            ]
        }

        signals = build_signals(payload, region="US", category="20")
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].platform, "youtube")
        self.assertEqual(signals[0].external_id, "youtube-abc123")
        self.assertIn("youtube.com/watch?v=abc123", signals[0].url)
        self.assertEqual(signals[0].author, "PlayLab")
        self.assertIn("cozy", signals[0].tags)
        self.assertGreater(signals[0].engagement, 0)

    def test_compute_engagement_score_is_bounded(self) -> None:
        score = compute_engagement_score(view_count=10_000_000, like_count=500_000, comment_count=20_000)
        self.assertLessEqual(score, 100.0)
        self.assertGreater(score, 0.0)
