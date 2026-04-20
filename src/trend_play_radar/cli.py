from __future__ import annotations

import argparse
import sys
from pathlib import Path

from trend_play_radar.config import get_config
from trend_play_radar.pipeline.cluster import cluster_signals
from trend_play_radar.pipeline.collect import collect_signals
from trend_play_radar.pipeline.report import write_reports
from trend_play_radar.pipeline.score import score_topics
from trend_play_radar.storage import Storage


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Trend Play Radar")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ["collect", "run"]:
        subparser = subparsers.add_parser(name)
        subparser.add_argument("--connectors", default="mock", help="Comma-separated connector names")
        subparser.add_argument("--json-input", help="Path to a JSON file for the json connector")
        subparser.add_argument("--keywords", default="", help="Comma-separated watchlist keywords")

    subparsers.add_parser("analyze")

    report_parser = subparsers.add_parser("report")
    report_parser.add_argument("--limit", type=int, default=10)
    return parser


def main(argv: list[str] | None = None) -> int:
    config = get_config()
    parser = build_parser()
    args = parser.parse_args(argv)
    storage = Storage(config.database_path)

    try:
        if args.command in {"collect", "run"}:
            connector_names = [item.strip() for item in args.connectors.split(",") if item.strip()]
            json_input = Path(args.json_input) if args.json_input else None
            keywords = [item.strip() for item in args.keywords.split(",") if item.strip()]
            signals = collect_signals(
                connector_names,
                project_root=config.project_root,
                json_input=json_input,
                keywords=keywords,
            )
            count = storage.upsert_signals(signals)
            print(f"Stored {count} signals in {config.database_path}")
            if args.command == "collect":
                return 0

        if args.command in {"analyze", "run"}:
            signals = storage.load_signals()
            topics = score_topics(cluster_signals(signals))
            storage.replace_topics(topics)
            print(f"Scored {len(topics)} topics")
            if args.command == "analyze":
                return 0

        if args.command in {"report", "run"}:
            limit = getattr(args, "limit", config.default_report_limit)
            if args.command == "run":
                topics = score_topics(cluster_signals(storage.load_signals()))
            else:
                topics = [topic_from_record(record) for record in storage.load_topics()]
                topics = sorted(topics, key=lambda topic: topic.final_priority_score, reverse=True)
            markdown_path, json_path = write_reports(topics, config.output_dir, limit=limit)
            print(f"Wrote reports to {markdown_path} and {json_path}")

        return 0
    finally:
        storage.close()


def topic_from_record(record: dict):
    from trend_play_radar.models import Topic

    return Topic(
        topic_key=record["topic_key"],
        label=record["label"],
        signals=[],
        platforms=record["platforms"],
        keywords=record["keywords"],
        current_window_count=record["current_window_count"],
        previous_window_count=record["previous_window_count"],
        baseline_window_average=record["baseline_window_average"],
        current_engagement=record["current_engagement"],
        previous_engagement=record["previous_engagement"],
        growth_ratio=record["growth_ratio"],
        engagement_growth_ratio=record["engagement_growth_ratio"],
        burst_score=record["burst_score"],
        growth_score=record["growth_score"],
        spread_score=record["spread_score"],
        confirmation_score=record["confirmation_score"],
        confidence_score=record["confidence_score"],
        game_fit_score=record["game_fit_score"],
        marketing_fit_score=record["marketing_fit_score"],
        production_feasibility_score=record["production_feasibility_score"],
        execution_fit_score=record["execution_fit_score"],
        final_priority_score=record["final_priority_score"],
        classification=record["classification"],
        spike_risk=record["spike_risk"],
        suggested_game_formats=record["suggested_game_formats"],
        suggested_marketing_hooks=record["suggested_marketing_hooks"],
        notes=record["notes"],
        evidence=record.get("evidence", []),
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
