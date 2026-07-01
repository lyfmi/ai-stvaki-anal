"""Guardrails: vision team validation and synthesis scrubbing against hallucinated teams."""
from __future__ import annotations

import re

from app.schemas import AnalysisResult, PremiumInsights, SearchPayload, VisionPayload

# Teams models often hallucinate for World Cup screenshots
_BLOCKED_TEAMS = frozenset(
    {
        "france",
        "франция",
        "франции",
        "францию",
        "germany",
        "германия",
        "германии",
        "argentina",
        "аргентина",
        "аргентины",
        "spain",
        "испания",
        "england",
        "англия",
        "portugal",
        "португалия",
        "italy",
        "италия",
        "netherlands",
        "нидерланды",
        "belgium",
        "бельгия",
    }
)

_NOTES_TEAM_ALIASES: dict[str, tuple[str, ...]] = {
    "brazil": ("brazil", "бразилия", "бразил"),
    "japan": ("japan", "япония", "япон"),
    "germany": ("germany", "германия"),
    "paraguay": ("paraguay", "парагвай"),
}


def _norm(value: str | None) -> str:
    return (value or "").strip().lower()


def _mentions_blocked(team: str | None) -> bool:
    return _norm(team) in _BLOCKED_TEAMS


def _notes_mention_team(notes: str, canonical: str) -> bool:
    aliases = _NOTES_TEAM_ALIASES.get(canonical, (canonical,))
    notes_l = notes.lower()
    return any(alias in notes_l for alias in aliases)


_PLACEHOLDER_TEAM_PATTERNS = (
    r"^home$",
    r"^away$",
    r"^team\s*a$",
    r"^team\s*b$",
    r"^team\s*1$",
    r"^team\s*2$",
    r"^opponent$",
    r"^домашн",
    r"^гостев",
    r"^хозяев",
    r"^команда\s*1$",
    r"^команда\s*2$",
    r"^команда\s*а$",
    r"^команда\s*б$",
)


def is_placeholder_team(name: str | None) -> bool:
    text = _norm(name)
    if not text:
        return True
    return any(re.search(pattern, text) for pattern in _PLACEHOLDER_TEAM_PATTERNS)


def vision_teams_valid(vision: VisionPayload) -> bool:
    home = (vision.home_team or "").strip()
    away = (vision.away_team or "").strip()
    if not home or not away or home.lower() == away.lower():
        return False
    if is_placeholder_team(home) or is_placeholder_team(away):
        return False
    return True


def vision_needs_retry(vision: VisionPayload) -> bool:
    home = _norm(vision.home_team)
    away = _norm(vision.away_team)
    notes = vision.screenshot_notes or ""

    if not home or not away or home == away:
        return True
    if is_placeholder_team(vision.home_team) or is_placeholder_team(vision.away_team):
        return True
    if vision.parse_confidence in ("low", "failed"):
        return True
    if vision.odds_on_screenshot and not vision.available_outcomes:
        return True

    if _mentions_blocked(vision.home_team) or _mentions_blocked(vision.away_team):
        # Notes mention different teams than extracted home/away
        for canonical in _NOTES_TEAM_ALIASES:
            if _notes_mention_team(notes, canonical):
                if canonical not in (home, away) and not home.startswith(canonical[:4]):
                    return True

    # e.g. notes say Brazil vs Japan but teams are France / Opponent
    if _notes_mention_team(notes, "brazil") and "brazil" not in home and "бразил" not in home:
        return True
    if _notes_mention_team(notes, "japan") and "japan" not in away and "япон" not in away:
        return True

    return False


VISION_STRICT_REPAIR = """RE-READ the cropped image carefully.
Extract ONLY the two team names printed on the match card in the crop.
Copy odds digits EXACTLY from the 1/X/2 row.
If the card shows Brazil vs Japan, output Brazil and Japan — NOT France or any other country.
Return the same JSON schema."""


def filter_search_for_teams(search: SearchPayload, home: str | None, away: str | None) -> SearchPayload:
    from app.services.ai.match_context import _blob_mentions_teams

    home = (home or "").strip()
    away = (away or "").strip()
    if not home or not away:
        return search

    filtered = [
        item
        for item in search.results
        if _blob_mentions_teams(f"{item.title} {item.snippet}", home, away)
    ]
    if not filtered:
        return search
    return SearchPayload(
        queries_executed=search.queries_executed,
        results=filtered[:8],
        search_status=search.search_status,
    )


def _text_has_foreign_team(text: str, home: str, away: str) -> bool:
    allowed = {_norm(home), _norm(away)}
    blob = text.lower()
    for blocked in _BLOCKED_TEAMS:
        if blocked in blob and blocked not in allowed:
            return True
    return False


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        text = item.strip()
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
    return out


def _mentions_team(text: str, team: str | None) -> bool:
    team = _norm(team)
    if not team:
        return False
    lower = text.lower()
    if team in lower:
        return True
    tokens = [t for t in re.split(r"[\s\-.]+", team) if len(t) > 2]
    if tokens and all(token in lower for token in tokens):
        return True
    if "congo" in team and "congo" in lower:
        return True
    return False


def side_hint_home(rec_l: str, home: str, away: str) -> bool:
    if _mentions_team(rec_l, away) and not _mentions_team(rec_l, home):
        return False
    return True


def _redact_foreign_teams(text: str, home: str, away: str) -> str:
    allowed = {_norm(home), _norm(away)}
    out = text
    for blocked in sorted(_BLOCKED_TEAMS, key=len, reverse=True):
        if blocked in allowed:
            continue
        if blocked not in out.lower():
            continue
        replacement = home if side_hint_home(out.lower(), home, away) else away
        out = re.sub(re.escape(blocked), replacement, out, flags=re.IGNORECASE)
    return out


def _scrub_text(text: str, home: str, away: str, user_lang: str) -> str:
    if not text or not _text_has_foreign_team(text, home, away):
        return text
    redacted = _redact_foreign_teams(text, home, away)
    if not _text_has_foreign_team(redacted, home, away):
        return redacted
    if user_lang.startswith("ru"):
        return f"Анализ матча {home} — {away} на основе данных со скриншота и актуальной формы."
    return f"Analysis for {home} vs {away} based on screenshot data and recent form."


def _fix_premium_teams(premium: PremiumInsights | None, home: str, away: str) -> PremiumInsights | None:
    if premium is None:
        return None
    allowed = {_norm(home), _norm(away)}
    bars = list(premium.form_bars)
    for idx, bar in enumerate(bars):
        if _norm(bar.team) not in allowed:
            bar.team = home if idx == 0 else away
    if premium.h2h and _text_has_foreign_team(premium.h2h, home, away):
        premium.h2h = f"{home} — {away}: очные встречи учтены в общем анализе."
    trends = [t for t in premium.trends if not _text_has_foreign_team(t, home, away)]
    advanced = [a for a in premium.advanced_arguments if not _text_has_foreign_team(a, home, away)]
    return premium.model_copy(
        update={
            "form_bars": bars,
            "trends": trends,
            "advanced_arguments": advanced,
        }
    )


def enforce_authoritative_teams(
    result: AnalysisResult,
    home: str | None,
    away: str | None,
    *,
    user_lang: str = "ru",
) -> AnalysisResult:
    home = (home or "").strip()
    away = (away or "").strip()
    if not home or not away:
        return result

    if result.explanation:
        result.explanation = _scrub_text(result.explanation, home, away, user_lang)
    if result.arguments:
        scrubbed = [
            _redact_foreign_teams(arg, home, away)
            if _text_has_foreign_team(arg, home, away)
            else arg.strip()
            for arg in result.arguments
            if arg.strip()
        ]
        result.arguments = _dedupe_preserve_order(scrubbed)
    result.premium_insights = _fix_premium_teams(result.premium_insights, home, away)

    from app.services.ai.odds_resolver import anchor_teams_in_recommendation

    result = anchor_teams_in_recommendation(result, home, away, user_lang=user_lang)
    return result
