import os
import subprocess
import sys
import json
import tempfile
from pathlib import Path
from unittest import TestCase


class SmokeTest(TestCase):
    def test_run_pipeline(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            env = dict(os.environ)
            env["PYTHONPATH"] = str(project_root / "src")
            env["TREND_PLAY_RADAR_OUTPUT_DIR"] = temp_dir
            result = subprocess.run(
                [sys.executable, "-m", "trend_play_radar", "run", "--fresh", "--connectors", "mock"],
                cwd=project_root,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            report_path = Path(temp_dir) / "latest_report.json"
            payload = json.loads(report_path.read_text())
            topics = payload["topics"]
            self.assertTrue(topics)
            self.assertIn("published_at", payload)
            self.assertIn("confidence_score", topics[0])
            self.assertIn("execution_fit_score", topics[0])

    def test_run_automatic_connectors(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            env = dict(os.environ)
            env["PYTHONPATH"] = str(project_root / "src")
            env["TREND_PLAY_RADAR_OUTPUT_DIR"] = temp_dir
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "trend_play_radar",
                    "run",
                    "--fresh",
                    "--connectors",
                    "rss,google_trends",
                    "--rss-feeds",
                    "data/sample_feed.xml",
                    "--trends-bridge",
                    "data/sample_google_trends.json",
                ],
                cwd=project_root,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_publish_bridge_parser_exists(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(project_root / "src")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "trend_play_radar",
                "publish-trends-bridge",
                "--help",
            ],
            cwd=project_root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_publish_report_parser_exists(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(project_root / "src")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "trend_play_radar",
                "publish-report",
                "--help",
            ],
            cwd=project_root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
