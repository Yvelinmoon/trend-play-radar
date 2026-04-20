from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


UTC = timezone.utc


def utcnow() -> datetime:
    return datetime.now(tz=UTC)


@dataclass(slots=True)
class RawSignal:
    platform: str
    external_id: str
    title: str
    url: str
    published_at: datetime
    engagement: float = 0.0
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)
    author: str = ""
    keyword_hint: str = ""
    raw_payload: dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict[str, Any]:
        record = asdict(self)
        record["published_at"] = self.published_at.isoformat()
        return record


@dataclass(slots=True)
class Topic:
    topic_key: str
    label: str
    signals: list[RawSignal]
    platforms: list[str]
    keywords: list[str]
    current_window_count: int
    previous_window_count: int
    baseline_window_average: float
    current_engagement: float
    previous_engagement: float
    growth_ratio: float
    engagement_growth_ratio: float
    burst_score: float
    growth_score: float
    spread_score: float
    confirmation_score: float
    confidence_score: float
    game_fit_score: float
    marketing_fit_score: float
    production_feasibility_score: float
    execution_fit_score: float
    final_priority_score: float
    classification: str
    spike_risk: str
    suggested_game_formats: list[str]
    suggested_marketing_hooks: list[str]
    notes: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)

    def to_record(self) -> dict[str, Any]:
        return {
            "topic_key": self.topic_key,
            "label": self.label,
            "platforms": self.platforms,
            "keywords": self.keywords,
            "current_window_count": self.current_window_count,
            "previous_window_count": self.previous_window_count,
            "baseline_window_average": self.baseline_window_average,
            "current_engagement": self.current_engagement,
            "previous_engagement": self.previous_engagement,
            "growth_ratio": self.growth_ratio,
            "engagement_growth_ratio": self.engagement_growth_ratio,
            "burst_score": self.burst_score,
            "growth_score": self.growth_score,
            "spread_score": self.spread_score,
            "confirmation_score": self.confirmation_score,
            "confidence_score": self.confidence_score,
            "game_fit_score": self.game_fit_score,
            "marketing_fit_score": self.marketing_fit_score,
            "production_feasibility_score": self.production_feasibility_score,
            "execution_fit_score": self.execution_fit_score,
            "final_priority_score": self.final_priority_score,
            "classification": self.classification,
            "spike_risk": self.spike_risk,
            "suggested_game_formats": self.suggested_game_formats,
            "suggested_marketing_hooks": self.suggested_marketing_hooks,
            "notes": self.notes,
            "evidence": self.evidence,
            "signal_count": len(self.signals),
            "signal_ids": [signal.external_id for signal in self.signals],
        }
