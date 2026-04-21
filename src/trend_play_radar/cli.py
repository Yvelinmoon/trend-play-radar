from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen

from trend_play_radar.config import get_config
from trend_play_radar.google_trends_bridge import (
    GoogleTrendsBridgeError,
    TrendsQuery,
    TrendsBridgeOptions,
    build_bridge,
)
from trend_play_radar.pipeline.cluster import cluster_signals
from trend_play_radar.pipeline.collect import collect_signals
from trend_play_radar.pipeline.debug_sources import write_debug_sources
from trend_play_radar.pipeline.report import write_reports
from trend_play_radar.pipeline.score import score_topics
from trend_play_radar.storage import Storage

DEFAULT_USER_AGENT = "trend-play-radar/0.1"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Trend Play Radar")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ["collect", "run"]:
        subparser = subparsers.add_parser(name)
        subparser.add_argument("--connectors", default="mock", help="Comma-separated connector names")
        subparser.add_argument("--json-input", help="Path to a JSON file for the json connector")
        subparser.add_argument("--keywords", default="", help="Comma-separated watchlist keywords")
        subparser.add_argument("--rss-feeds", default="", help="Comma-separated RSS or Atom feed URLs/paths")
        subparser.add_argument("--trends-bridge", help="URL or file path returning Google Trends JSON data")
        subparser.add_argument(
            "--fresh",
            action="store_true",
            help="Clear stored signals and topic snapshots before collecting a new batch",
        )

    subparsers.add_parser("analyze")

    report_parser = subparsers.add_parser("report")
    report_parser.add_argument("--limit", type=int, default=10)

    trends_parser = subparsers.add_parser("build-trends-bridge")
    trends_parser.add_argument("--keywords", default="", help="Comma-separated watchlist keywords")
    trends_parser.add_argument("--out", help="Output path for the generated Google Trends bridge JSON")
    trends_parser.add_argument("--geo", help="Google Trends region code")
    trends_parser.add_argument("--language", help="Google Trends language/locale")
    trends_parser.add_argument("--tz", type=int, help="Google Trends timezone offset in minutes")
    trends_parser.add_argument("--timeframe", help="Google Trends timeframe, for example 'now 7-d'")

    publish_parser = subparsers.add_parser("publish-trends-bridge")
    publish_parser.add_argument("--bridge-url", required=True, help="Cloudflare bridge publish endpoint URL")
    publish_parser.add_argument("--bridge-secret", required=True, help="Secret for x-bridge-secret")
    publish_parser.add_argument("--input", required=True, help="Path to bridge JSON file to publish")

    report_publish_parser = subparsers.add_parser("publish-report")
    report_publish_parser.add_argument("--report-url", required=True, help="Cloudflare report publish endpoint URL")
    report_publish_parser.add_argument("--bridge-secret", required=True, help="Secret for x-bridge-secret")
    report_publish_parser.add_argument("--input", required=True, help="Path to latest_report.json to publish")

    debug_publish_parser = subparsers.add_parser("publish-debug-sources")
    debug_publish_parser.add_argument("--debug-url", required=True, help="Cloudflare debug publish endpoint URL")
    debug_publish_parser.add_argument("--bridge-secret", required=True, help="Secret for x-bridge-secret")
    debug_publish_parser.add_argument("--input", required=True, help="Path to latest_debug_sources.json to publish")
    return parser


def main(argv: list[str] | None = None) -> int:
    config = get_config()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "build-trends-bridge":
        keywords = [item.strip() for item in args.keywords.split(",") if item.strip()] or config.default_keywords
        output_path = Path(args.out) if args.out else config.default_trends_output_path
        query_map = (
            [
                {"topic_key": keyword.lower().replace(" ", "_"), "topic_label": keyword.title(), "queries": [keyword]}
                for keyword in keywords
            ]
            if [item.strip() for item in args.keywords.split(",") if item.strip()]
            else config.default_trends_topic_map
        )
        try:
            records = build_bridge(
                TrendsBridgeOptions(
                    queries=build_trends_queries(query_map),
                    output_path=output_path,
                    geo=args.geo or config.default_trends_geo,
                    language=args.language or config.default_trends_language,
                    timezone_offset=args.tz if args.tz is not None else config.default_trends_timezone,
                    timeframe=args.timeframe or config.default_trends_timeframe,
                )
            )
        except GoogleTrendsBridgeError as exc:
            print(f"Google Trends bridge failed: {exc}", file=sys.stderr)
            return 1
        print(f"Wrote {len(records)} Google Trends records to {output_path}")
        return 0

    if args.command == "publish-trends-bridge":
        payload = Path(args.input).read_text()
        request = Request(
            args.bridge_url,
            data=payload.encode("utf-8"),
            method="POST",
            headers={
                "content-type": "application/json",
                "x-bridge-secret": args.bridge_secret,
                "user-agent": DEFAULT_USER_AGENT,
            },
        )
        with urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
        result = json.loads(body)
        print(f"Published {len(result.get('records', []))} bridge records to {args.bridge_url}")
        return 0

    if args.command == "publish-report":
        payload = json.loads(Path(args.input).read_text())
        if isinstance(payload, list):
            payload = {"topics": payload}
        wrapped = json.dumps(payload, ensure_ascii=False)
        request = Request(
            args.report_url,
            data=wrapped.encode("utf-8"),
            method="POST",
            headers={
                "content-type": "application/json",
                "x-bridge-secret": args.bridge_secret,
                "user-agent": DEFAULT_USER_AGENT,
            },
        )
        with urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
        result = json.loads(body)
        print(f"Published {len(result.get('topics', []))} report topics to {args.report_url}")
        return 0

    if args.command == "publish-debug-sources":
        payload = Path(args.input).read_text()
        request = Request(
            args.debug_url,
            data=payload.encode("utf-8"),
            method="POST",
            headers={
                "content-type": "application/json",
                "x-bridge-secret": args.bridge_secret,
                "user-agent": DEFAULT_USER_AGENT,
            },
        )
        with urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
        result = json.loads(body)
        print(f"Published debug source payload with {len(result.get('platforms', {}))} platforms to {args.debug_url}")
        return 0

    storage = Storage(config.database_path)

    try:
        if args.command in {"collect", "run"}:
            if getattr(args, "fresh", False):
                storage.clear_all()
            connector_names = [item.strip() for item in args.connectors.split(",") if item.strip()]
            json_input = Path(args.json_input) if args.json_input else None
            keywords = [item.strip() for item in args.keywords.split(",") if item.strip()]
            rss_feeds = [item.strip() for item in args.rss_feeds.split(",") if item.strip()]
            trends_bridge = args.trends_bridge or config.default_trends_bridge
            if not rss_feeds:
                rss_feeds = config.default_rss_feeds
            if not keywords:
                keywords = config.default_keywords
            signals = collect_signals(
                connector_names,
                project_root=config.project_root,
                json_input=json_input,
                keywords=keywords,
                rss_feeds=rss_feeds,
                trends_bridge=trends_bridge,
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
                signals = storage.load_signals()
                topics = score_topics(cluster_signals(signals))
            else:
                topics = [topic_from_record(record) for record in storage.load_topics()]
                topics = sorted(topics, key=lambda topic: topic.final_priority_score, reverse=True)
            markdown_path, json_path = write_reports(topics, config.output_dir, limit=limit)
            if args.command == "run":
                debug_path = write_debug_sources(signals, config.output_dir)
                print(f"Wrote debug source snapshot to {debug_path}")
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
        trend_direction=record.get("trend_direction", "insufficient"),
        trend_summary=record.get("trend_summary", ""),
        trend_series=record.get("trend_series", []),
        suggested_game_formats=record["suggested_game_formats"],
        suggested_marketing_hooks=record["suggested_marketing_hooks"],
        notes=record["notes"],
        evidence=record.get("evidence", []),
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))


def build_trends_queries(topic_map: list[dict]) -> list[TrendsQuery]:
    queries: list[TrendsQuery] = []
    for topic in topic_map:
        topic_key = str(topic["topic_key"])
        topic_label = str(topic["topic_label"])
        for query in topic.get("queries", []):
            query_text = str(query).strip()
            if not query_text:
                continue
            queries.append(
                TrendsQuery(
                    topic_key=topic_key,
                    topic_label=topic_label,
                    query=query_text,
                    tags=list({*topic_label.lower().split(), *query_text.lower().split()}),
                )
            )
    return queries
