"""Match timing and analysis mode detection (MSK timezone)."""
from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.schemas import MatchContextOut, SearchPayload, VisionPayload

MSK = ZoneInfo("Europe/Moscow")

STATUS_LABELS = {
    "ru": {
        "pre_match": "Скоро",
        "live": "Идёт сейчас",
        "post_match": "Матч завершён",
    },
    "en": {
        "pre_match": "Upcoming",
        "live": "Live now",
        "post_match": "Match finished",
    },
}


def now_msk() -> datetime:
    return datetime.now(MSK)


def msk_date_key() -> str:
    return now_msk().strftime("%Y-%m-%d")


def format_datetime_msk(dt: datetime) -> str:
    return dt.astimezone(MSK).strftime("%d.%m.%Y %H:%M МСК")


def _parse_iso_datetime(value: str) -> datetime | None:
    text = value.strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except ValueError:
        return None


def _extract_datetime_from_search(search: SearchPayload) -> datetime | None:
    patterns = [
        r"(\d{1,2})[./](\d{1,2})[./](\d{2,4})\s+(\d{1,2}):(\d{2})",
        r"(\d{4})-(\d{2})-(\d{2})[T\s](\d{2}):(\d{2})",
    ]
    for item in search.results:
        text = f"{item.title} {item.snippet}"
        for pattern in patterns:
            match = re.search(pattern, text)
            if not match:
                continue
            groups = match.groups()
            try:
                if len(groups) == 5 and len(groups[0]) <= 2:
                    day, month, year, hour, minute = groups
                    year = int(year)
                    if year < 100:
                        year += 2000
                    dt = datetime(int(year), int(month), int(day), int(hour), int(minute), tzinfo=MSK)
                    return dt
                if len(groups) == 5:
                    year, month, day, hour, minute = groups
                    dt = datetime(int(year), int(month), int(day), int(hour), int(minute), tzinfo=MSK)
                    return dt
            except ValueError:
                continue
    return None


def _search_indicates_finished(search: SearchPayload) -> bool:
    finished_markers = (
        "final score",
        "full time",
        "ft ",
        " ended ",
        " finished ",
        "result:",
        "итог",
        "заверш",
        "финальный сч",
    )
    for item in search.results:
        blob = f"{item.title} {item.snippet}".lower()
        if any(marker in blob for marker in finished_markers):
            score = re.search(r"\b\d{1,2}\s*[-:]\s*\d{1,2}\b", blob)
            if score:
                return True
    return False


def _search_indicates_live(search: SearchPayload) -> bool:
    live_markers = ("live", "in-play", "in play", "идёт", "онлайн", " minute ", "'")
    for item in search.results:
        blob = f"{item.title} {item.snippet}".lower()
        if any(marker in blob for marker in live_markers):
            return True
    return False


def resolve_match_context(
    vision: VisionPayload,
    search: SearchPayload,
    *,
    user_lang: str = "ru",
    force_pre_match: bool = False,
) -> MatchContextOut:
    lang = "en" if user_lang.startswith("en") else "ru"
    labels = STATUS_LABELS[lang]

    kickoff: datetime | None = None
    if vision.match_datetime:
        kickoff = _parse_iso_datetime(vision.match_datetime)
    if kickoff is None:
        kickoff = _extract_datetime_from_search(search)

    now = now_msk()
    mode = "pre_match"

    if force_pre_match:
        mode = "pre_match"
    elif vision.match_status_hint == "finished" or _search_indicates_finished(search):
        mode = "post_match"
    elif vision.match_status_hint == "live" or _search_indicates_live(search):
        mode = "live"
    elif kickoff is not None:
        if kickoff <= now - timedelta(hours=2):
            mode = "post_match"
        elif kickoff <= now + timedelta(minutes=15) and kickoff >= now - timedelta(hours=2):
            mode = "live"
        else:
            mode = "pre_match"

    datetime_msk: str | None = None
    if kickoff is not None:
        datetime_msk = format_datetime_msk(kickoff)
    elif not vision.datetime_on_screenshot:
        datetime_msk = None

    return MatchContextOut(
        analysis_mode=mode,
        match_status_label=labels.get(mode, labels["pre_match"]),
        match_datetime_msk=datetime_msk,
    )


def build_smart_search_queries(vision: VisionPayload) -> list[str]:
    """Merge vision queries with auto-generated ones (priority order, deduped)."""
    home = (vision.home_team or "").strip()
    away = (vision.away_team or "").strip()
    pair = f"{home} vs {away}".strip()
    auto: list[str] = []

    if pair and pair != "vs":
        if not vision.datetime_on_screenshot:
            auto.append(f"{pair} kickoff time today MSK")
        if not vision.odds_on_screenshot:
            auto.append(f"{pair} betting odds")
        if vision.match_status_hint in ("finished", "unknown"):
            auto.append(f"{pair} result score final")

    merged: list[str] = []
    seen: set[str] = set()
    for q in auto + list(vision.search_queries):
        key = q.strip().lower()
        if key and key not in seen:
            seen.add(key)
            merged.append(q.strip())
    return merged
