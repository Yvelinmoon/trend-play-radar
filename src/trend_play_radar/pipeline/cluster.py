from __future__ import annotations

import math
import re
from collections import defaultdict

from trend_play_radar.models import RawSignal


STOPWORDS = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "to",
    "of",
    "for",
    "with",
    "into",
    "these",
    "this",
    "that",
    "back",
    "your",
    "every",
    "keep",
    "has",
    "was",
    "rise",
    "search",
    "searches",
    "turning",
    "creators",
    "posts",
    "climbing",
    "mode",
    "short",
    "side",
    "scrolling",
}

THEME_GROUPS = {
    "office-personality": {
        "office",
        "coworkers",
        "manager",
        "workplace",
        "quiz",
        "personality",
        "identity",
        "class",
        "classes",
        "character",
        "archetypes",
        "chaos",
        "brainrot",
    },
    "boss-fight-parody": {
        "boss",
        "fight",
        "combat",
        "parody",
        "manager",
        "attack",
        "phase",
        "weak",
        "side",
        "scrolling",
    },
    "routine-parody": {
        "routine",
        "goblin",
        "productivity",
        "daily",
        "cursed",
        "parody",
        "humor",
    },
    "dating-checklist": {
        "dating",
        "situationship",
        "checklist",
        "questions",
        "scorecard",
        "relationship",
        "flags",
        "flag",
    },
}


def cluster_signals(signals: list[RawSignal]) -> dict[str, list[RawSignal]]:
    buckets: dict[str, list[RawSignal]] = defaultdict(list)
    for signal in signals:
        key = derive_topic_key(signal)
        buckets[key].append(signal)
    return dict(buckets)


def derive_topic_key(signal: RawSignal) -> str:
    candidates = " ".join([signal.keyword_hint, signal.title, signal.summary, " ".join(signal.tags)])
    tokens = tokenize(candidates)
    if not tokens:
        return f"{signal.platform}:{signal.external_id}"

    thematic_key = derive_theme_key(tokens)
    if thematic_key is not None:
        return thematic_key

    top_tokens = sorted(tokens, key=lambda item: (-score_token(item), item))[:3]
    return "-".join(top_tokens)


def tokenize(value: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", value.lower())
    return [token for token in tokens if len(token) > 2 and token not in STOPWORDS]


def score_token(token: str) -> float:
    return math.log(len(token) + 1)


def derive_theme_key(tokens: list[str]) -> str | None:
    token_set = set(tokens)
    best_match: tuple[str, int] | None = None
    for theme_key, theme_tokens in THEME_GROUPS.items():
        overlap = len(token_set & theme_tokens)
        if overlap < 2:
            continue
        if best_match is None or overlap > best_match[1]:
            best_match = (theme_key, overlap)
    return best_match[0] if best_match else None
