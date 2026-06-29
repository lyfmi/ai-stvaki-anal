"""Extract featured fixtures from search snippets (fallback when AI pick fails)."""
from __future__ import annotations

import re
from datetime import datetime, timedelta

from app.schemas import SearchResultItem
from app.services.ai.match_context import format_datetime_msk, now_msk

TEAM_VS = re.compile(
    r"([A-ZÀ-ÖØ-Þ][A-Za-z\s\-'.]{2,40}?)\s+(?:v|vs)\.?\s+([A-ZÀ-ÖØ-Þ][A-Za-z\s\-'.]{2,40})",
    re.IGNORECASE,
)
KICKOFF_TIME = re.compile(
    r"(?:kick[- ]?off(?:\s+time)?|⏰|🕐|at)\s*(?:at\s+)?(\d{1,2}):(\d{2})\s*(?:\([^)]+\))?\s*(?:MSK|МСК|GMT|BST|SAST|UTC|KSA|Houston|ET|PT)?|"
    r"(?:GMT|UTC|MSK|МСК|BST|SAST|ET|PT)\s+(\d{1,2}):(\d{2})|"
    r"(\d{1,2}):(\d{2})\s*\(Houston\)",
    re.IGNORECASE,
)
DATE_DAY = re.compile(
    r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|"
    r"Mon|Tue|Wed|Thu|Fri|Sat|Sun),?\s+(\d{1,2})\s+"
    r"(January|February|March|April|May|June|July|August|September|October|November|December|"
    r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(?:\s+(\d{4}))?",
    re.IGNORECASE,
)
TIME_AMPM = re.compile(
    r"(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(AM|PM)\s*(ET|PT|BST|GMT|MSK|SAST)?",
    re.IGNORECASE,
)
DATE_MON = re.compile(
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})",
    re.IGNORECASE,
)
DATE_COMMA = re.compile(
    r"(January|February|March|April|May|June|July|August|September|October|November|December|"
    r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})",
    re.IGNORECASE,
)
DATE_DMY = re.compile(
    r"(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December|"
    r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})",
    re.IGNORECASE,
)
ISO_DATE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
LIVE_WINDOW_MINUTES = 130
STRONG_LIVE_MARKERS = ("in-play", "in play", "идёт", "live now", "match live", "live coverage")
FINISHED_MARKERS = (
    "final score",
    "full time",
    "ft ",
    "match report",
    "highlights",
    "live score",
    "recap",
    "ended",
)

SPORT_MARKERS = (
    "world cup",
    "fifa",
    "football",
    "soccer",
    "fixture",
    "kick-off",
    "kickoff",
    "round of 32",
    "bafana",
    "матч",
    "stadium",
    "knockout",
)

JUNK_WORDS = (
    "news",
    "times",
    "breaking",
    "stories",
    "politics",
    "reporting",
    "journal",
    "international",
    "nation",
    "latest",
    "youtube",
    "wikipedia",
    "whatsapp",
    "flashscore.com",
    "home of football",
    "espn.com/live",
)

MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def _is_sports_blob(blob: str) -> bool:
    lower = blob.lower()
    return any(marker in lower for marker in SPORT_MARKERS)


def _is_valid_team(name: str) -> bool:
    text = name.strip()
    if len(text) < 3 or len(text) > 45:
        return False
    lower = text.lower()
    if any(word in lower for word in JUNK_WORDS):
        return False
    if lower in {"team a", "team b", "football", "fifa"}:
        return False
    return bool(re.search(r"[a-zA-Zа-яА-Я]", text))


def _clean_team(name: str) -> str:
    text = re.sub(r"\s+", " ", name.strip())
    text = text.split("|")[0].strip()
    for prefix in ("where to watch", "how to watch", "watch", "live coverage of the"):
        if text.lower().startswith(prefix):
            text = text[len(prefix) :].strip()
    for suffix in ("live", "stream", "tv channel", "channel", "live score"):
        if text.lower().endswith(suffix):
            text = text[: -len(suffix)].strip()
    text = re.sub(r"\s+in$", "", text, flags=re.I)
    text = re.sub(
        r"\s+(Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sun|Mon|Tue|Wed|Thu|Fri|Sat|Sat)\.?$",
        "",
        text,
        flags=re.I,
    )
    if text.lower().startswith("bafana bafana"):
        text = "South Africa"
    text = text.strip(" |-")
    if len(text.split()) > 4:
        return ""
    if any(w in text.lower() for w in ("where", "watch", "stream", "channel", "coverage")):
        return ""
    return text if _is_valid_team(text) else ""


def _extract_date(blob: str, reference: datetime) -> tuple[int, int, int]:
    day, month, year = reference.day, reference.month, reference.year

    mon = DATE_MON.search(blob)
    if mon:
        month_name, day_s, year_s = mon.groups()
        return int(day_s), MONTHS.get(mon.group(1).lower()[:3], month), int(year_s)

    for pattern in (DATE_COMMA, DATE_DMY):
        match = pattern.search(blob)
        if match:
            if pattern is DATE_COMMA:
                month_name, day_s, year_s = match.groups()
            else:
                day_s, month_name, year_s = match.groups()
            return int(day_s), MONTHS.get(month_name.lower(), month), int(year_s)

    date_match = DATE_DAY.search(blob)
    if date_match:
        day = int(date_match.group(1))
        month = MONTHS.get(date_match.group(2).lower(), month)
        if date_match.group(3):
            year = int(date_match.group(3))
        return day, month, year

    iso = ISO_DATE.search(blob)
    if iso:
        return int(iso.group(3)), int(iso.group(2)), int(iso.group(1))

    return day, month, year


def _parse_kickoff_from_text(text: str, reference: datetime) -> datetime | None:
    blob = text.replace("–", "-")
    day, month, year = _extract_date(blob, reference)

    time_match = TIME_AMPM.search(blob)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2) or 0)
        ampm = time_match.group(3).upper()
        tz = (time_match.group(4) or "").upper()
        if ampm == "PM" and hour < 12:
            hour += 12
        if ampm == "AM" and hour == 12:
            hour = 0
        if tz == "ET":
            hour = (hour + 7) % 24
        elif tz == "PT":
            hour = (hour + 10) % 24
        elif tz == "SAST":
            hour += 1
        try:
            return reference.replace(
                year=year, month=month, day=day, hour=hour, minute=minute, second=0, microsecond=0
            )
        except ValueError:
            return None

    time_match = KICKOFF_TIME.search(blob)
    if not time_match:
        return None

    groups = time_match.groups()
    hour = int(groups[0] or groups[2] or groups[4])
    minute = int(groups[1] or groups[3] or groups[5])
    upper = blob.upper()
    if re.search(r"\d{1,2}:\d{2}\s*\(Houston\)", blob, re.I):
        hour = (hour + 8) % 24
    elif "GMT" in upper and "MSK" not in upper and "МСК" not in blob:
        hour = (hour + 3) % 24
    elif "BST" in upper:
        hour = (hour + 2) % 24
    elif "SAST" in upper:
        hour = hour + 1

    try:
        return reference.replace(
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0,
        )
    except ValueError:
        return None


def _fixture_day_before_today(blob: str, reference: datetime) -> bool:
    day, month, year = _extract_date(blob, reference)
    try:
        fixture_day = datetime(year, month, day, tzinfo=reference.tzinfo)
    except ValueError:
        return False
    return fixture_day.date() < reference.date()


def _is_live_blob(blob: str) -> bool:
    lower = blob.lower()
    if any(marker in lower for marker in ("wikipedia", "britannica", "preview", "ticketmaster", "buy ")):
        return False
    if any(marker in lower for marker in FINISHED_MARKERS):
        return False
    return any(marker in lower for marker in STRONG_LIVE_MARKERS)


def _score_fixture(home: str, away: str, kickoff: datetime | None, blob: str, now: datetime) -> float:
    if not _is_valid_team(home) or not _is_valid_team(away):
        return -1
    if home.lower() == away.lower():
        return -1

    score = 0.0
    lower = blob.lower()
    if "fifa.com" in lower:
        score += 50
    if "world cup" in lower:
        score += 35

    is_live = _is_live_blob(blob)
    if kickoff:
        if kickoff <= now < kickoff + timedelta(minutes=LIVE_WINDOW_MINUTES):
            score += 100
        elif kickoff > now and kickoff <= now + timedelta(hours=36):
            score += 60 - min(30, (kickoff - now).total_seconds() / 3600)
        else:
            return -1
    elif is_live:
        score += 80
    else:
        return -1

    if is_live and kickoff:
        score += 25
    return score


def pick_fixture_from_search(results: list[SearchResultItem]) -> dict | None:
    """Best-effort fixture extraction without LLM."""
    from app.services.debug_agent_log import agent_log

    now = now_msk()
    candidates: list[tuple[float, dict]] = []

    for item in results:
        blob = f"{item.title} {item.snippet} {item.url}"
        if not _is_sports_blob(blob):
            continue

        for match in TEAM_VS.finditer(blob):
            home = _clean_team(match.group(1))
            away = _clean_team(match.group(2))
            if not home or not away:
                continue

            text_blob = f"{item.title} {item.snippet}"
            if _fixture_day_before_today(text_blob, now):
                # #region agent log
                agent_log(
                    location="match_of_day_parser.py:pick",
                    message="skip past fixture date",
                    data={"home": home, "away": away, "title": item.title[:80]},
                    hypothesis_id="B",
                )
                # #endregion
                continue

            kickoff = _parse_kickoff_from_text(text_blob, now)
            if kickoff is None:
                # #region agent log
                agent_log(
                    location="match_of_day_parser.py:pick",
                    message="skip missing kickoff",
                    data={"home": home, "away": away, "title": item.title[:80]},
                    hypothesis_id="A",
                )
                # #endregion
                continue

            score = _score_fixture(home, away, kickoff, blob, now)
            if score < 10 or kickoff is None:
                continue

            league = "FIFA World Cup 2026" if "world cup" in blob.lower() else "Football"
            live_now = kickoff <= now < kickoff + timedelta(minutes=LIVE_WINDOW_MINUTES)
            if not live_now and kickoff <= now:
                continue

            candidates.append(
                (
                    score + (50 if live_now else 0),
                    {
                        "home_team": home,
                        "away_team": away,
                        "league": league,
                        "kickoff_msk": format_datetime_msk(kickoff),
                        "kickoff_at": kickoff.isoformat(),
                        "teaser": item.title[:120] or f"{home} — {away}",
                        "is_live": live_now,
                    },
                )
            )

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    winner = candidates[0][1]
    # #region agent log
    agent_log(
        location="match_of_day_parser.py:pick",
        message="picked fixture",
        data={
            "home": winner["home_team"],
            "away": winner["away_team"],
            "kickoff_msk": winner["kickoff_msk"],
            "is_live": winner["is_live"],
            "score": candidates[0][0],
        },
        hypothesis_id="C",
    )
    # #endregion
    return winner
