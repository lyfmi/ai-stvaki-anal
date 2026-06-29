"""Resolve betting coefficients from screenshot vision or 1win search snippets."""
from __future__ import annotations

import re

from app.schemas import AnalysisResult, SearchPayload, VisionPayload

_ODDS_NUM = re.compile(r"\b(\d(?:\.\d{1,2})?)\b")
_1WIN_MARKERS = ("1win", "1-win", "one-win", "one win", "1вин")


def _norm_team(name: str | None) -> str:
    return (name or "").strip().lower()


def _mentions_team(text: str, team: str | None) -> bool:
    team = _norm_team(team)
    if not team:
        return False
    return team in text.lower()


def _pick_home_away_draw(
    recommendation: str,
    home: str | None,
    away: str | None,
) -> str | None:
    rec = (recommendation or "").lower()
    if any(x in rec for x in ("ничья", "draw", " x ", "х ", "пx", "1x")):
        return "draw"
    if _mentions_team(rec, away) and not _mentions_team(rec, home):
        return "away"
    if _mentions_team(rec, home):
        return "home"
    if rec.strip() in {"1", "п1", "победа 1", "home"}:
        return "home"
    if rec.strip() in {"2", "п2", "победа 2", "away"}:
        return "away"
    return "home"


def coefficient_from_vision(
    vision: VisionPayload,
    recommendation: str,
) -> float | None:
    if not vision.odds_on_screenshot or not vision.available_outcomes:
        return None
    side = _pick_home_away_draw(recommendation, vision.home_team, vision.away_team)
    outcomes = vision.available_outcomes

    def _label_side(label: str) -> str | None:
        lab = label.strip().lower()
        if lab in {"1", "п1", "w1", "home"}:
            return "home"
        if lab in {"2", "п2", "w2", "away"}:
            return "away"
        if lab in {"x", "х", "draw", "ничья"}:
            return "draw"
        if _mentions_team(lab, vision.home_team):
            return "home"
        if _mentions_team(lab, vision.away_team):
            return "away"
        return None

    for outcome in outcomes:
        if outcome.coefficient is None:
            continue
        if _label_side(outcome.label) == side:
            return float(outcome.coefficient)

    for outcome in outcomes:
        if outcome.coefficient is not None:
            return float(outcome.coefficient)
    return None


def extract_1win_odds_from_search(
    search: SearchPayload,
    home: str,
    away: str,
) -> dict[str, float] | None:
    """Return {home, draw, away} odds only when snippet looks like 1win."""
    home_l, away_l = _norm_team(home), _norm_team(away)
    for item in search.results:
        blob = f"{item.title} {item.snippet} {item.url}"
        blob_l = blob.lower()
        if not any(m in blob_l for m in _1WIN_MARKERS):
            continue
        if home_l and home_l not in blob_l and away_l and away_l not in blob_l:
            continue
        nums = [float(m.group(1)) for m in _ODDS_NUM.finditer(blob) if 1.01 <= float(m.group(1)) <= 50]
        if len(nums) >= 3:
            return {"home": nums[0], "draw": nums[1], "away": nums[2]}
        if len(nums) == 1:
            return {"home": nums[0], "draw": 0.0, "away": 0.0}
    return None


def coefficient_from_1win_search(
    search: SearchPayload,
    home: str,
    away: str,
    recommendation: str,
) -> float | None:
    odds = extract_1win_odds_from_search(search, home, away)
    if not odds:
        return None
    side = _pick_home_away_draw(recommendation, home, away)
    if side == "draw" and odds.get("draw"):
        return odds["draw"]
    if side == "away" and odds.get("away"):
        return odds["away"]
    if odds.get("home"):
        return odds["home"]
    return None


def apply_odds_policy(
    result: AnalysisResult,
    *,
    vision: VisionPayload | None = None,
    search: SearchPayload | None = None,
    home: str | None = None,
    away: str | None = None,
) -> AnalysisResult:
    """Never keep invented odds — only screenshot or 1win search."""
    if result.analysis_mode == "post_match" or not result.is_betting_recommendation:
        result.coefficient = None
        result.probability_percent = None
        return result

    coef: float | None = None
    if vision is not None:
        coef = coefficient_from_vision(vision, result.recommendation or "")
    if coef is None and search is not None and home and away:
        coef = coefficient_from_1win_search(search, home, away, result.recommendation or "")

    result.coefficient = coef
    if coef is None:
        result.probability_percent = None
    return result


def anchor_teams_in_recommendation(
    result: AnalysisResult,
    home: str | None,
    away: str | None,
    *,
    user_lang: str = "ru",
) -> AnalysisResult:
    """Ensure recommendation references teams from screenshot/fixture, not hallucinated names."""
    home = (home or "").strip()
    away = (away or "").strip()
    if not home or not away:
        return result
    rec = (result.recommendation or "").strip()
    rec_l = rec.lower()
    allowed = {home.lower(), away.lower()}
    # Common wrong picks when user cropped Brazil-Japan
    for wrong in (
        "france",
        "франция",
        "франции",
        "францию",
        "germany",
        "германия",
        "германии",
        "argentina",
        "аргентина",
    ):
        if wrong in rec_l and wrong not in allowed:
            rec = rec.replace(wrong, home if side_hint_home(rec_l, home, away) else away)
            rec_l = rec.lower()

    if not any(t in rec_l for t in allowed):
        side = _pick_home_away_draw(rec, home, away)
        if user_lang.startswith("ru"):
            if side == "away":
                result.recommendation = f"П2 — Победа {away}"
            elif side == "draw":
                result.recommendation = f"X — Ничья {home} — {away}"
            else:
                result.recommendation = f"П1 — Победа {home}"
        else:
            if side == "away":
                result.recommendation = f"Away win — {away}"
            elif side == "draw":
                result.recommendation = f"Draw — {home} vs {away}"
            else:
                result.recommendation = f"Home win — {home}"
    else:
        result.recommendation = rec
    return result


def side_hint_home(rec_l: str, home: str, away: str) -> bool:
    if _mentions_team(rec_l, away) and not _mentions_team(rec_l, home):
        return False
    return True
