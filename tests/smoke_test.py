import os
import subprocess
import sys
import json
from pathlib import Path
from unittest import TestCase


class SmokeTest(TestCase):
    def test_run_pipeline(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(project_root / "src")
        result = subprocess.run(
            [sys.executable, "-m", "trend_play_radar", "run", "--connectors", "mock"],
            cwd=project_root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)

        report_path = project_root / "output" / "latest_report.json"
        payload = json.loads(report_path.read_text())
        self.assertTrue(payload)
        self.assertIn("confidence_score", payload[0])
        self.assertIn("execution_fit_score", payload[0])
