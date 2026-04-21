from __future__ import annotations

import html
from http.client import IncompleteRead
import hashlib
import re
import subprocess
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from trend_play_radar.connectors.base import Connector
from trend_play_radar.models import RawSignal


class RSSConnector(Connector):
    name = "rss"

    def fetch(self) -> list[RawSignal]:
        signals: list[RawSignal] = []
        for feed in self.context.rss_feeds:
            try:
                xml_bytes = read_resource(feed)
                signals.extend(parse_feed(xml_bytes, source=feed))
            except Exception:
                continue
        return signals


def read_resource(location: str) -> bytes:
    parsed = urlparse(location)
    if parsed.scheme in {"http", "https", "file"}:
        return read_http_resource(location)
    return open(location, "rb").read()


def read_http_resource(location: str) -> bytes:
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            request = Request(location, headers=request_headers())
            with urlopen(request, timeout=20) as response:
                return response.read()
        except IncompleteRead as error:
            if error.partial:
                return bytes(error.partial)
            last_error = error
        except Exception as error:
            last_error = error
        time.sleep(0.4 * (attempt + 1))

    curl_bytes = read_http_resource_with_curl(location)
    if curl_bytes:
        return curl_bytes

    if last_error is not None:
        raise last_error
    raise RuntimeError(f"Failed to read resource: {location}")


def read_http_resource_with_curl(location: str) -> bytes:
    result = subprocess.run(
        [
            "curl",
            "-sL",
            "--max-time",
            "25",
            "--retry",
            "2",
            "--retry-all-errors",
            "-H",
            f"User-Agent: {request_headers()['User-Agent']}",
            "-H",
            f"Accept: {request_headers()['Accept']}",
            location,
        ],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return b""
    return result.stdout


def request_headers() -> dict[str, str]:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/135.0.0.0 Safari/537.36 trend-play-radar/0.1"
        ),
        "Accept": "application/json,application/xml,text/xml,text/html,*/*",
    }


def parse_feed(xml_bytes: bytes, *, source: str) -> list[RawSignal]:
    root = ET.fromstring(xml_bytes)
    local_name = strip_ns(root.tag)
    if local_name == "rss":
        return parse_rss(root, source=source)
    if local_name == "feed":
        return parse_atom(root, source=source)
    return []


def parse_rss(root: ET.Element, *, source: str) -> list[RawSignal]:
    channel = root.find("channel")
    if channel is None:
        return []

    source_name = text_or_default(channel.find("title"), "rss")
    signals: list[RawSignal] = []
    for item in channel.findall("item"):
        raw_title = text_or_default(item.find("title"), "Untitled RSS item")
        plain_title = text_or_default(item.find("plainTitle"), "").strip()
        title = plain_title or clean_itch_title(raw_title)
        url = text_or_default(item.find("link"), source)
        summary = clean_summary(text_or_default(item.find("description"), ""))
        published_at = parse_datetime(text_or_default(item.find("pubDate"), ""))
        tags = dedupe_text(
            [
                *extract_title_labels(raw_title),
                *extract_platform_nodes(item.find("platforms")),
                *[node.text.strip() for node in item.findall("category") if node.text],
            ]
        )
        external_id = stable_external_id(source, title, url)
        signals.append(
            RawSignal(
                platform="rss",
                external_id=external_id,
                title=title,
                url=url,
                published_at=published_at,
                engagement=0.0,
                summary=summary,
                tags=tags,
                metrics={},
                author="",
                keyword_hint=build_keyword_hint(title=title, summary=summary, tags=tags),
                raw_payload={
                    "source": source,
                    "source_name": source_name,
                    "raw_title": raw_title,
                    "plain_title": plain_title or title,
                    "price": text_or_default(item.find("price"), ""),
                    "platform_tags": extract_platform_nodes(item.find("platforms")),
                },
            )
        )
    return signals


def parse_atom(root: ET.Element, *, source: str) -> list[RawSignal]:
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    source_name = text_or_default(root.find("atom:title", ns), "atom")
    signals: list[RawSignal] = []
    for entry in root.findall("atom:entry", ns):
        title = text_or_default(entry.find("atom:title", ns), "Untitled Atom entry")
        link = entry.find("atom:link[@rel='alternate']", ns) or entry.find("atom:link", ns)
        url = link.attrib.get("href", source) if link is not None else source
        summary = text_or_default(entry.find("atom:summary", ns), text_or_default(entry.find("atom:content", ns), ""))
        published_at = parse_datetime(
            text_or_default(entry.find("atom:published", ns), text_or_default(entry.find("atom:updated", ns), ""))
        )
        tags = [node.attrib.get("term", "").strip() for node in entry.findall("atom:category", ns) if node.attrib.get("term")]
        external_id = stable_external_id(source, title, url)
        signals.append(
            RawSignal(
                platform="rss",
                external_id=external_id,
                title=title,
                url=url,
                published_at=published_at,
                engagement=0.0,
                summary=summary,
                tags=tags,
                metrics={},
                author="",
                keyword_hint=" ".join(tags[:3]),
                raw_payload={"source": source, "source_name": source_name},
            )
        )
    return signals


def parse_datetime(value: str) -> datetime:
    if not value:
        return datetime.now(tz=timezone.utc)
    try:
        parsed = parsedate_to_datetime(value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except Exception:
        pass
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.now(tz=timezone.utc)


def strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1]


def text_or_default(node: ET.Element | None, default: str) -> str:
    if node is None or node.text is None:
        return default
    return node.text.strip()


def clean_itch_title(value: str) -> str:
    if not value:
        return "Untitled RSS item"
    cleaned = re.sub(r"\s*\[[^\]]+\]", "", value).strip()
    return html.unescape(cleaned) or "Untitled RSS item"


def extract_title_labels(value: str) -> list[str]:
    if not value:
        return []
    labels = [label.strip().lower() for label in re.findall(r"\[([^\]]+)\]", value)]
    return [normalize_tag(label) for label in labels if is_meaningful_tag(label)]


def extract_platform_nodes(node: ET.Element | None) -> list[str]:
    if node is None:
        return []
    tags: list[str] = []
    for child in list(node):
        local = strip_ns(child.tag).lower()
        if child.text and child.text.strip().lower() == "yes":
            tags.append(normalize_tag(local))
    return tags


def clean_summary(value: str) -> str:
    if not value:
        return ""
    text = re.sub(r"<img\b[^>]*>", " ", value, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_keyword_hint(*, title: str, summary: str, tags: list[str]) -> str:
    parts = [title, *tags[:4]]
    if summary:
        parts.append(summary[:120])
    return " ".join(parts)


def dedupe_text(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        normalized = normalize_tag(item)
        if not normalized or normalized in seen or not is_meaningful_tag(normalized):
            continue
        seen.add(normalized)
        output.append(normalized)
    return output


def normalize_tag(value: str) -> str:
    return value.strip().lower().replace("-", " ")


def is_meaningful_tag(value: str) -> bool:
    normalized = normalize_tag(value)
    return normalized not in {"free", "html", "windows", "linux", "macos", "android"} and len(normalized) > 1


def stable_external_id(source: str, title: str, url: str) -> str:
    digest = hashlib.sha1(f"{source}|{title}|{url}".encode("utf-8")).hexdigest()
    return f"rss-{digest[:16]}"
