from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from trend_play_radar.models import Topic


def write_reports(topics: list[Topic], output_dir: Path, *, limit: int) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    trimmed = topics if limit <= 0 else topics[:limit]
    generated_at = datetime.now(tz=timezone.utc)

    markdown_path = output_dir / "latest_report.md"
    json_path = output_dir / "latest_report.json"
    batch_id = generated_at.strftime("%Y%m%d-%H%M%S-%f")
    history_dir = output_dir / "history" / batch_id
    history_dir.mkdir(parents=True, exist_ok=True)
    history_markdown_path = history_dir / "report.md"
    history_json_path = history_dir / "report.json"

    markdown = render_markdown(trimmed, generated_at=generated_at)
    report_payload = {
        "published_at": generated_at.isoformat(),
        "topics": [topic.to_record() for topic in trimmed],
    }

    markdown_path.write_text(markdown)
    json_path.write_text(json.dumps(report_payload, ensure_ascii=False, indent=2))
    history_markdown_path.write_text(markdown)
    history_json_path.write_text(json.dumps(report_payload, ensure_ascii=False, indent=2))
    write_history_index(
        output_dir / "history",
        batch_id=batch_id,
        generated_at=generated_at,
        topic_count=len(trimmed),
    )
    return markdown_path, json_path


def render_markdown(topics: list[Topic], *, generated_at: datetime) -> str:
    lines = [
        "# Trend Play Radar Report",
        "",
        f"_Published at {generated_at.isoformat()}_",
        "",
    ]
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


def write_history_index(
    history_root: Path, *, batch_id: str, generated_at: datetime, topic_count: int
) -> None:
    index_path = history_root / "index.json"
    entries: list[dict] = []
    if index_path.exists():
        entries = json.loads(index_path.read_text())

    entries.insert(
        0,
        {
            "batch_id": batch_id,
            "published_at": generated_at.isoformat(),
            "topic_count": topic_count,
            "json_path": f"history/{batch_id}/report.json",
            "markdown_path": f"history/{batch_id}/report.md",
        },
    )
    index_path.write_text(json.dumps(entries[:200], ensure_ascii=False, indent=2))
