from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from trend_play_radar.models import RawSignal


def write_debug_sources(signals: list[RawSignal], output_dir: Path, *, sample_size: int = 5) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "published_at": datetime.now(tz=timezone.utc).isoformat(),
        "signal_count": len(signals),
        "platforms": {},
    }

    grouped: dict[str, list[RawSignal]] = defaultdict(list)
    for signal in signals:
        grouped[signal.platform].append(signal)

    for platform, items in grouped.items():
        samples = sorted(items, key=lambda item: item.published_at, reverse=True)[:sample_size]
        payload["platforms"][platform] = {
            "count": len(items),
            "samples": [
                {
                    "external_id": signal.external_id,
                    "title": signal.title,
                    "url": signal.url,
                    "published_at": signal.published_at.isoformat(),
                    "engagement": signal.engagement,
                    "summary": signal.summary,
                    "tags": signal.tags,
                    "keyword_hint": signal.keyword_hint,
                    "raw_payload": signal.raw_payload,
                }
                for signal in samples
            ],
        }

    path = output_dir / "latest_debug_sources.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    return path
