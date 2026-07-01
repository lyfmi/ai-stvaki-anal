"""Display names for national teams and leagues by user language."""
from __future__ import annotations

import re

TEAM_NAMES_RU: dict[str, str] = {
    "england": "Англия",
    "congo dr": "ДР Конго",
    "dr congo": "ДР Конго",
    "democratic republic of the congo": "ДР Конго",
    "brazil": "Бразилия",
    "japan": "Япония",
    "south africa": "ЮАР",
    "canada": "Канада",
    "usa": "США",
    "united states": "США",
    "mexico": "Мексика",
    "france": "Франция",
    "germany": "Германия",
    "spain": "Испания",
    "argentina": "Аргентина",
    "portugal": "Португалия",
    "netherlands": "Нидерланды",
    "belgium": "Бельгия",
    "croatia": "Хорватия",
    "morocco": "Марокко",
    "senegal": "Сенегал",
    "uruguay": "Уругвай",
    "colombia": "Колумбия",
    "ecuador": "Эквадор",
    "switzerland": "Швейцария",
    "austria": "Австрия",
    "scotland": "Шотландия",
    "wales": "Уэльс",
    "norway": "Норвегия",
    "paraguay": "Парагвай",
    "bosnia and herzegovina": "Босния и Герцеговина",
    "bosnia": "Босния и Герцеговина",
    "korea republic": "Южная Корея",
    "south korea": "Южная Корея",
    "saudi arabia": "Саудовская Аравия",
    "australia": "Австралия",
    "iran": "Иран",
    "qatar": "Катар",
    "tunisia": "Тунис",
    "ghana": "Гана",
    "cameroon": "Камерун",
    "poland": "Польша",
    "serbia": "Сербия",
    "denmark": "Дания",
    "sweden": "Швеция",
    "italy": "Италия",
    "turkey": "Турция",
    "ukraine": "Украина",
    "czech republic": "Чехия",
    "czechia": "Чехия",
}

LEAGUE_NAMES_RU: dict[str, str] = {
    "fifa world cup 2026": "ЧМ-2026",
    "football": "Футбол",
}


def _team_key(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


def localize_team_name(name: str, lang: str) -> str:
    if not name or lang.startswith("en"):
        return name
    return TEAM_NAMES_RU.get(_team_key(name), name)


def localize_league_name(name: str, lang: str) -> str:
    if not name or lang.startswith("en"):
        return name
    return LEAGUE_NAMES_RU.get(_team_key(name), name)


def localize_match_dict(match: dict, lang: str) -> dict:
    if lang.startswith("en"):
        return match
    out = dict(match)
    if out.get("home_team"):
        out["home_team"] = localize_team_name(str(out["home_team"]), lang)
    if out.get("away_team"):
        out["away_team"] = localize_team_name(str(out["away_team"]), lang)
    if out.get("league"):
        out["league"] = localize_league_name(str(out["league"]), lang)
    return out
