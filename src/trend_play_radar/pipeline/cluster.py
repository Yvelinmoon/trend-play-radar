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
    "img",
    "free",
    "src",
    "https",
    "http",
    "itch",
    "itchio",
    "google",
    "trends",
    "signal",
    "quot",
    "windows",
    "linux",
    "macos",
    "html",
    "other",
    "game",
    "games",
    "play",
    "yes",
    "confirms",
    "broadening",
    "escaping",
    "latest",
    "score",
    "scores",
    "average",
    "samples",
    "searches",
    "interest",
    "topic",
    "isolated",
}

THEME_GROUPS = {
    "personality-quiz": {
        "label": "Personality Quiz",
        "keywords": ["personality", "quiz", "identity", "character"],
        "tokens": {
            "office",
            "coworkers",
            "manager",
            "workplace",
            "quiz",
            "personality",
            "identity",
            "alignment",
            "chart",
            "class",
            "classes",
            "character",
            "archetypes",
            "archetype",
            "fandom",
            "picker",
            "brainrot",
            "test",
        },
    },
    "dating-checklist": {
        "label": "Dating Checklist",
        "keywords": ["dating", "checklist", "relationship", "scorecard"],
        "tokens": {
            "dating",
            "situationship",
            "checklist",
            "questions",
            "scorecard",
            "relationship",
            "flags",
            "flag",
            "red",
        },
    },
    "cozy-puzzle": {
        "label": "Cozy Puzzle",
        "keywords": ["cozy", "puzzle", "wholesome", "relaxing"],
        "tokens": {
            "cozy",
            "puzzle",
            "wholesome",
            "relaxing",
            "story",
            "mystery",
            "novel",
        },
    },
    "merge-idle": {
        "label": "Merge Idle",
        "keywords": ["merge", "idle", "incremental", "builder"],
        "tokens": {
            "merge",
            "idle",
            "incremental",
            "sim",
            "simulation",
            "builder",
        },
    },
    "management-sim": {
        "label": "Management Sim",
        "keywords": ["management", "simulation", "builder", "tycoon"],
        "tokens": {
            "management",
            "manager",
            "simulation",
            "sim",
            "builder",
            "tycoon",
            "shop",
            "station",
            "business",
            "colony",
            "houses",
            "restaurant",
        },
    },
    "arcade-shooter": {
        "label": "Arcade Shooter",
        "keywords": ["shooter", "arcade", "action", "twin-stick"],
        "tokens": {
            "shooter",
            "shoot",
            "bullet",
            "arcade",
            "blaster",
            "blasters",
            "twin",
            "stick",
            "combat",
            "action",
        },
    },
    "precision-platformer": {
        "label": "Precision Platformer",
        "keywords": ["platformer", "precision", "action", "jump"],
        "tokens": {
            "platformer",
            "platforming",
            "precision",
            "jump",
            "runner",
            "metroidvania",
            "parkour",
        },
    },
    "card-strategy": {
        "label": "Card Strategy",
        "keywords": ["card", "strategy", "deck", "tactics"],
        "tokens": {
            "card",
            "cards",
            "deck",
            "chess",
            "strategy",
            "tactics",
            "tactical",
            "autobattler",
            "casino",
            "poker",
        },
    },
    "visual-novel-story": {
        "label": "Visual Novel Story",
        "keywords": ["visual", "novel", "story", "narrative"],
        "tokens": {
            "visual",
            "novel",
            "story",
            "narrative",
            "dialogue",
            "romance",
        },
    },
    "horror-exploration": {
        "label": "Horror Exploration",
        "keywords": ["horror", "exploration", "mystery", "adventure"],
        "tokens": {
            "horror",
            "exploration",
            "underworld",
            "nightmare",
            "dark",
            "cave",
            "dungeon",
            "haunted",
            "mystery",
        },
    },
    "educational-sim": {
        "label": "Educational Sim",
        "keywords": ["educational", "simulation", "learning", "management"],
        "tokens": {
            "educational",
            "education",
            "learning",
            "recycle",
            "recycling",
            "school",
            "management",
        },
    },
}

TOPIC_METADATA = THEME_GROUPS


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
    best_match: tuple[str, int, int] | None = None
    for theme_key, metadata in THEME_GROUPS.items():
        theme_tokens = metadata["tokens"]
        overlap = len(token_set & theme_tokens)
        if overlap < 2:
            continue
        token_count = len(theme_tokens)
        if best_match is None or overlap > best_match[1] or (overlap == best_match[1] and token_count < best_match[2]):
            best_match = (theme_key, overlap, token_count)
    return best_match[0] if best_match else None


def topic_label_for_key(topic_key: str) -> str | None:
    metadata = TOPIC_METADATA.get(topic_key)
    return metadata["label"] if metadata else None


def topic_keywords_for_key(topic_key: str) -> list[str]:
    metadata = TOPIC_METADATA.get(topic_key)
    return list(metadata["keywords"]) if metadata else []
