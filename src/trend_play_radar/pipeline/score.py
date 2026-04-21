from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from math import ceil

from trend_play_radar.models import RawSignal, Topic, utcnow
from trend_play_radar.pipeline.cluster import tokenize


CURRENT_WINDOW = timedelta(hours=24)
PREVIOUS_WINDOW = timedelta(hours=24)
BASELINE_DAYS = 7

GAME_FORMAT_RULES = {
    "quiz": "personality quiz",
    "personality": "personality quiz",
    "identity": "personality quiz",
    "boss": "side-scrolling boss fight",
    "fight": "side-scrolling boss fight",
    "combat": "side-scrolling boss fight",
    "parody": "timed reaction challenge",
    "routine": "timed reaction challenge",
    "character": "class sorter",
    "office": "class sorter",
    "dating": "scorecard test",
    "checklist": "scorecard test",
}

HOOK_RULES = {
    "quiz": "Find out which role you really are",
    "personality": "Share your result card before your friends do",
    "boss": "Beat the boss everyone knows from real life",
    "fight": "Can you survive the final phase",
    "office": "Every team has one. Which one are you",
    "routine": "Rate how cursed your daily loop has become",
    "dating": "See how many red flags your result unlocks",
    "checklist": "Turn private panic into a shareable scorecard",
}


def score_topics(clustered_signals: dict[str, list[RawSignal]]) -> list[Topic]:
    topics = [build_topic(topic_key, signals) for topic_key, signals in clustered_signals.items()]
    return sorted(topics, key=lambda topic: topic.final_priority_score, reverse=True)


def build_topic(topic_key: str, signals: list[RawSignal]) -> Topic:
    reference_time = max((signal.published_at for signal in signals), default=utcnow())
    keywords = extract_keywords(signals)
    platform_counts = Counter(signal.platform for signal in signals)

    current_signals, previous_signals, baseline_signals = split_windows(signals, reference_time)
    current_window_count = len(current_signals)
    previous_window_count = len(previous_signals)
    baseline_window_average = compute_baseline_average(baseline_signals, reference_time)
    current_engagement = sum(signal.engagement for signal in current_signals)
    previous_engagement = sum(signal.engagement for signal in previous_signals)

    growth_ratio = compute_growth_ratio(current_window_count, previous_window_count, baseline_window_average)
    engagement_growth_ratio = compute_growth_ratio(
        current_engagement,
        previous_engagement,
        compute_engagement_baseline(baseline_signals, reference_time),
    )

    burst_score = score_burst(current_window_count, baseline_window_average)
    growth_score = score_growth(growth_ratio, engagement_growth_ratio)
    spread_score = score_spread(platform_counts)
    confirmation_score = score_confirmation(signals, platform_counts)
    confidence_score = round(min(burst_score + growth_score + spread_score + confirmation_score, 100.0), 1)

    game_fit_score = round(score_game_fit(keywords), 1)
    marketing_fit_score = round(score_marketing_fit(keywords), 1)
    production_feasibility_score = round(score_production_feasibility(keywords), 1)
    content_quality_score = round(score_content_quality(signals, keywords), 1)
    execution_fit_score = round(
        min(game_fit_score + marketing_fit_score + production_feasibility_score + content_quality_score, 100.0), 1
    )

    final_priority_score = round(confidence_score * 0.6 + execution_fit_score * 0.4, 1)
    spike_risk = assess_spike_risk(
        current_window_count=current_window_count,
        previous_window_count=previous_window_count,
        platform_counts=platform_counts,
        has_search_confirmation="google_trends" in platform_counts,
    )
    classification = classify_topic(
        confidence_score=confidence_score,
        execution_fit_score=execution_fit_score,
        spike_risk=spike_risk,
        has_search_confirmation="google_trends" in platform_counts,
    )
    trend_series = build_trend_series(signals, reference_time)
    trend_direction = assess_trend_direction(trend_series)
    trend_summary = build_trend_summary(
        trend_series=trend_series,
        trend_direction=trend_direction,
        current_window_count=current_window_count,
        previous_window_count=previous_window_count,
        has_search_confirmation="google_trends" in platform_counts,
    )

    suggested_game_formats = suggest_game_formats(keywords)
    suggested_marketing_hooks = suggest_marketing_hooks(keywords)
    notes = build_notes(
        current_window_count=current_window_count,
        previous_window_count=previous_window_count,
        baseline_window_average=baseline_window_average,
        growth_ratio=growth_ratio,
        confidence_score=confidence_score,
        execution_fit_score=execution_fit_score,
        classification=classification,
        spike_risk=spike_risk,
    )
    evidence = build_evidence(
        signals=signals,
        platform_counts=platform_counts,
        current_window_count=current_window_count,
        previous_window_count=previous_window_count,
        baseline_window_average=baseline_window_average,
        current_engagement=current_engagement,
        previous_engagement=previous_engagement,
        growth_ratio=growth_ratio,
        engagement_growth_ratio=engagement_growth_ratio,
    )

    return Topic(
        topic_key=topic_key,
        label=build_label(keywords),
        signals=signals,
        platforms=sorted(platform_counts),
        keywords=keywords,
        current_window_count=current_window_count,
        previous_window_count=previous_window_count,
        baseline_window_average=round(baseline_window_average, 2),
        current_engagement=round(current_engagement, 1),
        previous_engagement=round(previous_engagement, 1),
        growth_ratio=round(growth_ratio, 2),
        engagement_growth_ratio=round(engagement_growth_ratio, 2),
        burst_score=round(burst_score, 1),
        growth_score=round(growth_score, 1),
        spread_score=round(spread_score, 1),
        confirmation_score=round(confirmation_score, 1),
        confidence_score=confidence_score,
        game_fit_score=game_fit_score,
        marketing_fit_score=marketing_fit_score,
        production_feasibility_score=production_feasibility_score,
        execution_fit_score=execution_fit_score,
        final_priority_score=final_priority_score,
        classification=classification,
        spike_risk=spike_risk,
        trend_direction=trend_direction,
        trend_summary=trend_summary,
        trend_series=trend_series,
        suggested_game_formats=suggested_game_formats,
        suggested_marketing_hooks=suggested_marketing_hooks,
        notes=notes,
        evidence=evidence,
    )


def split_windows(
    signals: list[RawSignal], reference_time: datetime
) -> tuple[list[RawSignal], list[RawSignal], list[RawSignal]]:
    current_start = reference_time - CURRENT_WINDOW
    previous_start = current_start - PREVIOUS_WINDOW
    baseline_start = previous_start - timedelta(days=BASELINE_DAYS)

    current = [signal for signal in signals if current_start <= signal.published_at <= reference_time]
    previous = [signal for signal in signals if previous_start <= signal.published_at < current_start]
    baseline = [signal for signal in signals if baseline_start <= signal.published_at < previous_start]
    return current, previous, baseline


def compute_baseline_average(signals: list[RawSignal], reference_time: datetime) -> float:
    if not signals:
        return 0.0

    buckets = [0 for _ in range(BASELINE_DAYS)]
    baseline_start = reference_time - CURRENT_WINDOW - PREVIOUS_WINDOW - timedelta(days=BASELINE_DAYS)
    for signal in signals:
        offset = signal.published_at - baseline_start
        index = int(offset.total_seconds() // 86400)
        if 0 <= index < BASELINE_DAYS:
            buckets[index] += 1
    non_empty_buckets = [count for count in buckets if count > 0]
    if not non_empty_buckets:
        return 0.0
    return sum(non_empty_buckets) / len(non_empty_buckets)


def compute_engagement_baseline(signals: list[RawSignal], reference_time: datetime) -> float:
    if not signals:
        return 0.0

    buckets = [0.0 for _ in range(BASELINE_DAYS)]
    baseline_start = reference_time - CURRENT_WINDOW - PREVIOUS_WINDOW - timedelta(days=BASELINE_DAYS)
    for signal in signals:
        offset = signal.published_at - baseline_start
        index = int(offset.total_seconds() // 86400)
        if 0 <= index < BASELINE_DAYS:
            buckets[index] += signal.engagement
    non_empty_buckets = [count for count in buckets if count > 0]
    if not non_empty_buckets:
        return 0.0
    return sum(non_empty_buckets) / len(non_empty_buckets)


def compute_growth_ratio(current: float, previous: float, baseline: float) -> float:
    reference = max(previous, baseline, 1.0)
    return current / reference


def score_burst(current_window_count: int, baseline_window_average: float) -> float:
    if current_window_count == 0:
        return 0.0
    baseline_reference = max(baseline_window_average, 1.0)
    burst_ratio = current_window_count / baseline_reference
    return min(ceil(burst_ratio * 8.0), 20.0)


def score_growth(growth_ratio: float, engagement_growth_ratio: float) -> float:
    score = 0.0
    if growth_ratio >= 1.2:
        score += min((growth_ratio - 1.0) * 12.0, 14.0)
    if engagement_growth_ratio >= 1.1:
        score += min((engagement_growth_ratio - 1.0) * 4.0, 6.0)
    return min(score, 20.0)


def score_spread(platform_counts: Counter[str]) -> float:
    score = min(len(platform_counts) * 6.0, 18.0)
    if "reddit" in platform_counts and "google_trends" in platform_counts:
        score += 4.0
    return min(score, 22.0)


def score_confirmation(signals: list[RawSignal], platform_counts: Counter[str]) -> float:
    score = 0.0
    if "google_trends" in platform_counts:
        score += 8.0
    if len(signals) >= 3:
        score += 3.0
    if unique_authors(signals) >= 2:
        score += 2.0
    return min(score, 15.0)


def score_game_fit(keywords: list[str]) -> float:
    total = 0.0
    for keyword in keywords:
        if keyword in {"quiz", "personality", "identity", "boss", "fight", "character", "office"}:
            total += 7.0
        elif keyword in {"parody", "routine", "meme", "shareable", "dating", "checklist"}:
            total += 5.0
        else:
            total += 1.5
    return min(total, 35.0)


def score_marketing_fit(keywords: list[str]) -> float:
    total = 0.0
    for keyword in keywords:
        if keyword in {"meme", "identity", "office", "boss", "dating"}:
            total += 5.0
        elif keyword in {"character", "parody", "quiz", "checklist"}:
            total += 3.5
        else:
            total += 1.0
    return min(total, 25.0)


def score_production_feasibility(keywords: list[str]) -> float:
    fast_formats = {"quiz", "personality", "identity", "office", "character", "routine", "dating", "checklist"}
    heavier_formats = {"combat", "boss", "fight"}
    if any(keyword in fast_formats for keyword in keywords):
        return 20.0
    if any(keyword in heavier_formats for keyword in keywords):
        return 14.0
    return 12.0


def score_content_quality(signals: list[RawSignal], keywords: list[str]) -> float:
    title_lengths = [len(signal.title.split()) for signal in signals if signal.title]
    meaningful_summaries = [signal for signal in signals if len(signal.summary.strip()) >= 24]
    genre_keywords = {
        "puzzle",
        "cozy",
        "merge",
        "idle",
        "wholesome",
        "visual",
        "novel",
        "adventure",
        "simulation",
        "sports",
        "action",
        "platformer",
        "metroidvania",
        "survival",
        "management",
        "educational",
        "shooter",
    }

    score = 0.0
    if meaningful_summaries:
        score += 4.0
    if any(length >= 2 for length in title_lengths):
        score += 2.0
    if any(keyword in genre_keywords for keyword in keywords):
        score += 4.0
    return min(score, 10.0)


def classify_topic(
    *,
    confidence_score: float,
    execution_fit_score: float,
    spike_risk: str,
    has_search_confirmation: bool,
) -> str:
    if (
        confidence_score >= 48
        and execution_fit_score >= 42
        and (has_search_confirmation or spike_risk == "low")
    ):
        return "high-confidence candidate"
    if confidence_score >= 30 and execution_fit_score >= 32:
        return "watchlist candidate"
    return "low-confidence or noisy"


def assess_spike_risk(
    *,
    current_window_count: int,
    previous_window_count: int,
    platform_counts: Counter[str],
    has_search_confirmation: bool,
) -> str:
    if current_window_count >= 3 and previous_window_count == 0 and len(platform_counts) == 1:
        return "high"
    if current_window_count >= 2 and not has_search_confirmation:
        return "medium"
    return "low"


def extract_keywords(signals: list[RawSignal]) -> list[str]:
    counts: Counter[str] = Counter()
    for signal in signals:
        counts.update(tokenize(" ".join([signal.keyword_hint, signal.title, signal.summary, *signal.tags])))
    priority_tokens = {"quiz", "personality", "fandom", "character", "cozy", "puzzle", "merge", "idle", "wholesome", "visual", "novel", "adventure", "simulation", "sports", "action"}
    ranked = sorted(
        counts.items(),
        key=lambda item: (0 if item[0] in priority_tokens else 1, -item[1], -len(item[0]), item[0]),
    )
    return [token for token, _ in ranked[:6]]


def build_trend_series(signals: list[RawSignal], reference_time: datetime) -> list[dict]:
    google_points = build_google_trends_series(signals)
    if google_points:
        return google_points
    return build_signal_count_series(signals, reference_time)


def build_google_trends_series(signals: list[RawSignal]) -> list[dict]:
    series_pool: list[list[dict]] = []
    for signal in signals:
        raw_series = signal.raw_payload.get("raw_payload", {}).get("series") or signal.raw_payload.get("series")
        if not raw_series:
            continue
        series_pool.append(raw_series)

    if not series_pool:
        return []

    longest = max(series_pool, key=len)
    points: list[dict] = []
    for index, point in enumerate(longest):
        values = []
        for series in series_pool:
            if index < len(series):
                values.append(float(series[index].get("value", 0)))
        if not values:
            continue
        label = point.get("formatted_time") or point.get("formattedTime") or str(index + 1)
        points.append({"label": label, "value": round(sum(values) / len(values), 2)})

    if len(points) <= 8:
        return points

    step = max(len(points) // 8, 1)
    sampled = [points[index] for index in range(0, len(points), step)]
    return sampled[-8:]


def build_signal_count_series(signals: list[RawSignal], reference_time: datetime) -> list[dict]:
    end = reference_time.astimezone(timezone.utc)
    start = end - timedelta(days=6)
    buckets = {day_index: 0 for day_index in range(7)}
    labels = []
    for day_index in range(7):
        day = (start + timedelta(days=day_index)).date()
        labels.append(day.strftime("%m-%d"))

    for signal in signals:
        signal_time = signal.published_at.astimezone(timezone.utc)
        delta_days = (signal_time.date() - start.date()).days
        if 0 <= delta_days < 7:
            buckets[delta_days] += 1

    return [{"label": labels[index], "value": buckets[index]} for index in range(7)]


def assess_trend_direction(series: list[dict]) -> str:
    if len(series) < 3:
        return "insufficient"

    values = [float(point.get("value", 0)) for point in series]
    latest = values[-1]
    previous_avg = sum(values[-3:-1]) / max(len(values[-3:-1]), 1)
    early_avg = sum(values[:-2]) / max(len(values[:-2]), 1) if len(values) > 2 else previous_avg

    if latest >= max(previous_avg * 1.6, early_avg * 1.8, 2):
        return "spiking"
    if latest > previous_avg * 1.15:
        return "rising"
    if latest < previous_avg * 0.75 and previous_avg > 0:
        return "cooling"
    if max(values) <= 1:
        return "weak"
    return "steady"


def build_trend_summary(
    *,
    trend_series: list[dict],
    trend_direction: str,
    current_window_count: int,
    previous_window_count: int,
    has_search_confirmation: bool,
) -> str:
    if not trend_series:
        return "No time trend available yet."
    if trend_direction == "spiking":
        return "Recent points jump sharply above the earlier baseline."
    if trend_direction == "rising":
        return "Recent points are trending upward over the last few intervals."
    if trend_direction == "cooling":
        return "This topic had activity earlier, but the latest interval cooled off."
    if trend_direction == "steady":
        if has_search_confirmation:
            return "Search demand is holding at a relatively stable level."
        return "Recent intervals are relatively flat without a breakout."
    if trend_direction == "weak":
        return "Signal is present, but the timeline is still thin."
    return f"Current window {current_window_count} vs previous {previous_window_count}."


def build_label(keywords: list[str]) -> str:
    return " ".join(keyword.capitalize() for keyword in keywords[:3]) or "Untitled Trend"


def suggest_game_formats(keywords: list[str]) -> list[str]:
    formats: list[str] = []
    for keyword in keywords:
        maybe_format = GAME_FORMAT_RULES.get(keyword)
        if maybe_format and maybe_format not in formats:
            formats.append(maybe_format)
    return formats or ["interactive microgame"]


def suggest_marketing_hooks(keywords: list[str]) -> list[str]:
    hooks: list[str] = []
    for keyword in keywords:
        maybe_hook = HOOK_RULES.get(keyword)
        if maybe_hook and maybe_hook not in hooks:
            hooks.append(maybe_hook)
    return hooks or ["Turn the trend into a result worth sharing"]


def build_notes(
    *,
    current_window_count: int,
    previous_window_count: int,
    baseline_window_average: float,
    growth_ratio: float,
    confidence_score: float,
    execution_fit_score: float,
    classification: str,
    spike_risk: str,
) -> list[str]:
    return [
        f"Current 24h signals: {current_window_count}",
        f"Previous 24h signals: {previous_window_count}",
        f"Baseline daily average: {baseline_window_average:.2f}",
        f"Growth ratio vs baseline/previous: {growth_ratio:.2f}",
        f"Confidence {confidence_score:.1f}, execution fit {execution_fit_score:.1f}",
        f"Classification: {classification}; spike risk: {spike_risk}",
    ]


def build_evidence(
    *,
    signals: list[RawSignal],
    platform_counts: Counter[str],
    current_window_count: int,
    previous_window_count: int,
    baseline_window_average: float,
    current_engagement: float,
    previous_engagement: float,
    growth_ratio: float,
    engagement_growth_ratio: float,
) -> list[str]:
    evidence = [
        f"{current_window_count} current-window signals vs {previous_window_count} in the previous 24h window",
        f"Baseline average is {baseline_window_average:.2f} signals per day over the prior {BASELINE_DAYS} days",
        f"Current engagement {current_engagement:.1f} vs previous-window engagement {previous_engagement:.1f}",
        f"Signal growth ratio {growth_ratio:.2f}; engagement growth ratio {engagement_growth_ratio:.2f}",
        f"Observed on {len(platform_counts)} platforms: {', '.join(sorted(platform_counts))}",
    ]
    if "google_trends" in platform_counts:
        evidence.append("Search validation exists via Google Trends")
    if unique_authors(signals) > 1:
        evidence.append(f"Signals come from {unique_authors(signals)} distinct authors or trend IDs")
    return evidence


def unique_authors(signals: list[RawSignal]) -> int:
    authors = {signal.author for signal in signals if signal.author}
    if authors:
        return len(authors)
    return len({signal.external_id for signal in signals})
