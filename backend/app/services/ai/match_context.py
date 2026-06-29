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


def parse_kickoff_msk(text: str, reference: datetime | None = None) -> datetime | None:
    """Parse kickoff string like '21:00 МСК' or '28.06.2026 21:00 МСК'."""
    reference = reference or now_msk()
    raw = text.strip().replace("MSK", "МСК").replace("мск", "МСК")
    raw = re.sub(r"\s+", " ", raw)

    full = re.match(
        r"^(\d{1,2})[./](\d{1,2})[./](\d{2,4})\s+(\d{1,2}):(\d{2})(?:\s*МСК)?$",
        raw,
        re.IGNORECASE,
    )
    if full:
        day, month, year, hour, minute = full.groups()
        year = int(year)
        if year < 100:
            year += 2000
        try:
            return datetime(int(year), int(month), int(day), int(hour), int(minute), tzinfo=MSK)
        except ValueError:
            return None

    time_only = re.match(r"^(\d{1,2}):(\d{2})(?:\s*МСК)?$", raw, re.IGNORECASE)
    if time_only:
        hour, minute = int(time_only.group(1)), int(time_only.group(2))
        candidate = reference.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate < reference - timedelta(hours=6):
            candidate += timedelta(days=1)
        return candidate

    return _parse_iso_datetime(raw)


def is_kickoff_expired(kickoff: datetime | None, *, live_buffer_minutes: int = 120) -> bool:
    """Match of the day slot expired after kickoff + buffer."""
    if kickoff is None:
        return False
    return now_msk() >= kickoff + timedelta(minutes=live_buffer_minutes)


def is_kickoff_upcoming(kickoff: datetime | None, *, min_minutes_ahead: int = -15) -> bool:
    """True if kickoff is still relevant (not long finished)."""
    if kickoff is None:
        return True
    return kickoff >= now_msk() - timedelta(minutes=min_minutes_ahead)


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


def _extract_datetime_from_search(search: SearchPayload, home: str = "", away: str = "") -> datetime | None:
    patterns = [
        r"(\d{1,2})[./](\d{1,2})[./](\d{2,4})\s+(\d{1,2}):(\d{2})",
        r"(\d{4})-(\d{2})-(\d{2})[T\s](\d{2}):(\d{2})",
    ]
    for item in search.results:
        text = f"{item.title} {item.snippet}"
        if home or away:
            if not _blob_mentions_teams(text, home, away):
                continue
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


def _blob_mentions_teams(blob: str, home: str, away: str) -> bool:
    if not home and not away:
        return True
    blob_l = blob.lower()
    home_l = home.strip().lower()
    away_l = away.strip().lower()
    if home_l and home_l in blob_l:
        return True
    if away_l and away_l in blob_l:
        return True
    if home_l and away_l:
        pair = f"{home_l} vs {away_l}"
        if pair in blob_l or f"{home_l} - {away_l}" in blob_l:
            return True
    return False


def _search_indicates_finished(search: SearchPayload, home: str = "", away: str = "") -> bool:
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
        blob = f"{item.title} {item.snippet}"
        if not _blob_mentions_teams(blob, home, away):
            continue
        blob_l = blob.lower()
        if any(marker in blob_l for marker in finished_markers):
            score = re.search(r"\b\d{1,2}\s*[-:]\s*\d{1,2}\b", blob)
            if score:
                return True
    return False


def _search_indicates_live(search: SearchPayload, home: str = "", away: str = "") -> bool:
    live_markers = ("live", "in-play", "in play", "идёт", "онлайн", " minute ", "'")
    for item in search.results:
        blob = f"{item.title} {item.snippet}"
        if not _blob_mentions_teams(blob, home, away):
            continue
        blob_l = blob.lower()
        if any(marker in blob_l for marker in live_markers):
            return True
    return False


def _resolve_mode_from_kickoff(kickoff: datetime | None, now: datetime) -> str:
    """Kickoff is authoritative for pre/live/post when known."""
    if kickoff is None:
        return "pre_match"
    if kickoff > now + timedelta(minutes=10):
        return "pre_match"
    if kickoff <= now - timedelta(minutes=130):
        return "post_match"
    if kickoff <= now < kickoff + timedelta(minutes=130):
        return "live"
    return "pre_match"


def resolve_match_context_from_fixture(
    match: dict,
    *,
    user_lang: str = "ru",
) -> MatchContextOut:
    """Authoritative status from featured match kickoff (not search noise)."""
    lang = "en" if user_lang.startswith("en") else "ru"
    labels = STATUS_LABELS[lang]

    kickoff: datetime | None = None
    kickoff_raw = match.get("kickoff_at")
    if kickoff_raw:
        try:
            kickoff = datetime.fromisoformat(str(kickoff_raw).replace("Z", "+00:00"))
            if kickoff.tzinfo is None:
                kickoff = kickoff.replace(tzinfo=MSK)
        except ValueError:
            kickoff = None
    if kickoff is None and match.get("kickoff_msk"):
        kickoff = parse_kickoff_msk(str(match["kickoff_msk"]))

    now = now_msk()
    mode = _resolve_mode_from_kickoff(kickoff, now)
    if mode == "pre_match" and kickoff is None and match.get("is_live"):
        mode = "live"

    datetime_msk = format_datetime_msk(kickoff) if kickoff else match.get("kickoff_msk")

    return MatchContextOut(
        analysis_mode=mode,
        match_status_label=labels.get(mode, labels["pre_match"]),
        match_datetime_msk=datetime_msk,
    )


def resolve_match_context(
    vision: VisionPayload,
    search: SearchPayload,
    *,
    user_lang: str = "ru",
    force_pre_match: bool = False,
) -> MatchContextOut:
    lang = "en" if user_lang.startswith("en") else "ru"
    labels = STATUS_LABELS[lang]
    home = (vision.home_team or "").strip()
    away = (vision.away_team or "").strip()

    kickoff: datetime | None = None
    if vision.match_datetime:
        kickoff = _parse_iso_datetime(vision.match_datetime)
        if kickoff is None:
            kickoff = parse_kickoff_msk(vision.match_datetime)
    if kickoff is None:
        kickoff = _extract_datetime_from_search(search, home, away)

    now = now_msk()

    if vision.match_status_hint == "finished" or (vision.final_score and vision.final_score.strip()):
        mode = "post_match"
    elif kickoff is not None:
        mode = _resolve_mode_from_kickoff(kickoff, now)
    elif force_pre_match:
        mode = "pre_match"
    elif _search_indicates_finished(search, home, away):
        mode = "post_match"
    elif vision.match_status_hint == "live" or (
        vision.match_status_hint != "upcoming" and _search_indicates_live(search, home, away)
    ):
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
            auto.append(f"{pair} kickoff time MSK today")
            auto.append(f"{pair} матч время МСК")
        if not vision.odds_on_screenshot:
            auto.append(f"{pair} betting odds 1win")
        if vision.match_status_hint in ("finished", "unknown"):
            auto.append(f"{pair} result score final")
            auto.append(f"{pair} прогноз статистика")

    merged: list[str] = []
    seen: set[str] = set()
    for q in auto + list(vision.search_queries):
        key = q.strip().lower()
        if key and key not in seen:
            seen.add(key)
            merged.append(q.strip())
    return merged
