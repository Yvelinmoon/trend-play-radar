from __future__ import annotations

import json
from pathlib import Path

from trend_play_radar.models import Topic


def write_reports(topics: list[Topic], output_dir: Path, *, limit: int) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    trimmed = topics[:limit]

    markdown_path = output_dir / "latest_report.md"
    json_path = output_dir / "latest_report.json"

    markdown_path.write_text(render_markdown(trimmed))
    json_path.write_text(
        json.dumps([topic.to_record() for topic in trimmed], ensure_ascii=False, indent=2)
    )
    return markdown_path, json_path


def render_markdown(topics: list[Topic]) -> str:
    lines = ["# Trend Play Radar Report", ""]
    if not topics:
        lines.append("No topics available.")
        return "\n".join(lines) + "\n"

    for index, topic in enumerate(topics, start=1):
        lines.extend(
            [
                f"## {index}. {topic.label}",
                "",
                f"- Classification: {topic.classification}",
                f"- Final priority score: {topic.final_priority_score}",
                f"- Confidence score: {topic.confidence_score}",
                f"- Execution fit score: {topic.execution_fit_score}",
                f"- Spike risk: {topic.spike_risk}",
                f"- Platforms: {', '.join(topic.platforms)}",
                f"- Keywords: {', '.join(topic.keywords)}",
                f"- Current window vs previous: {topic.current_window_count} vs {topic.previous_window_count}",
                f"- Baseline daily average: {topic.baseline_window_average}",
                f"- Growth ratio: {topic.growth_ratio}",
                f"- Suggested game formats: {', '.join(topic.suggested_game_formats)}",
                f"- Suggested hooks: {', '.join(topic.suggested_marketing_hooks)}",
                f"- Notes: {'; '.join(topic.notes)}",
                f"- Evidence: {'; '.join(topic.evidence)}",
                "",
            ]
        )
    return "\n".join(lines)
