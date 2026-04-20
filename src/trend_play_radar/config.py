from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class AppConfig:
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parents[2])
    output_dir: Path = field(init=False)
    database_path: Path = field(init=False)
    default_report_limit: int = 10

    def __post_init__(self) -> None:
        self.output_dir = self.project_root / "output"
        self.database_path = self.output_dir / "trend_play_radar.db"
        self.output_dir.mkdir(parents=True, exist_ok=True)


def get_config() -> AppConfig:
    return AppConfig()
