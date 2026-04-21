import json
from pathlib import Path
import sys
from unittest import TestCase

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from trend_play_radar.google_trends_bridge import (
    GoogleTrendsBridgeError,
    TrendsBridgeOptions,
    TrendsQuery,
    build_bridge,
    extract_series,
    parse_trends_json,
)


class GoogleTrendsBridgeTest(TestCase):
    def test_parse_trends_json_strips_xssi_prefix(self) -> None:
        payload = parse_trends_json(")]}',\n{\"widgets\":[]}")
        self.assertEqual(payload, {"widgets": []})

    def test_extract_series(self) -> None:
        timeline = [
            {"time": "1", "formattedTime": "A", "value": [12, 34]},
            {"time": "2", "formattedTime": "B", "value": [20, 50]},
        ]
        series = extract_series(timeline, keyword_index=1)
        self.assertEqual(series[0]["value"], 34)
        self.assertEqual(series[1]["formatted_time"], "B")

    def test_build_bridge_with_mocked_requests(self) -> None:
        output_path = Path("/tmp/trend-play-radar-trends-test.json")
        responses = iter(
            [
                {"widgets": [{"id": "TIMESERIES", "token": "abc", "request": {"time": "now 7-d"}}]},
                {
                    "default": {
                        "timelineData": [
                            {"time": "1", "formattedTime": "A", "value": [10, 20]},
                            {"time": "2", "formattedTime": "B", "value": [40, 50]},
                        ]
                    }
                },
            ]
        )

        from trend_play_radar import google_trends_bridge as module

        original = module.trends_api_request
        module.trends_api_request = lambda **_: next(responses)
        try:
            records = build_bridge(
                TrendsBridgeOptions(
                    queries=[
                        TrendsQuery(
                            topic_key="brainrot_meme",
                            topic_label="Brainrot Meme",
                            query="brainrot meme",
                            tags=["brainrot", "meme"],
                        ),
                        TrendsQuery(
                            topic_key="cozy_puzzle",
                            topic_label="Cozy Puzzle",
                            query="cozy game",
                            tags=["cozy", "game"],
                        ),
                    ],
                    output_path=output_path,
                )
            )
        finally:
            module.trends_api_request = original

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["trend_score"], 40)
        self.assertEqual(records[0]["parent_topic"], "brainrot_meme")
        self.assertEqual(records[1]["topic_label"], "Cozy Puzzle")
        self.assertTrue(output_path.exists())
        payload = json.loads(output_path.read_text())
        self.assertEqual(payload[1]["keyword"], "cozy game")

    def test_bridge_error_type(self) -> None:
        error = GoogleTrendsBridgeError("rate limited")
        self.assertEqual(str(error), "rate limited")
