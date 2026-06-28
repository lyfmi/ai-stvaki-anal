import re
from typing import Any

from pydantic import ValidationError

from app.schemas import AnalysisResult

REQUIRED_FIELDS = (
    "recommendation",
    "market",
    "coefficient",
    "probability_percent",
    "risk",
    "arguments",
    "confidence",
    "explanation",
)

FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "recommendation": (
        "recommendation",
        "recommend",
        "pick",
        "bet",
        "selection",
        "outcome",
        "ставка",
        "рекомендация",
        "выбор",
    ),
    "market": ("market", "market_type", "тип_ставки", "рынок"),
    "coefficient": ("coefficient", "odds", "coef", "коэффициент", "кф"),
    "probability_percent": (
        "probability_percent",
        "probability",
        "prob",
        "вероятность",
        "probability_pct",
    ),
    "risk": ("risk", "risk_level", "риск"),
    "arguments": ("arguments", "reasons", "pros", "аргументы", "причины"),
    "confidence": ("confidence", "conf", "уверенность"),
    "explanation": ("explanation", "summary", "comment", "объяснение", "комментарий"),
}


def _flatten_dict(data: dict[str, Any]) -> dict[str, Any]:
    flat = dict(data)
    for key in ("result", "analysis", "response", "data", "output"):
        nested = data.get(key)
        if isinstance(nested, dict):
            flat.update(nested)
    return flat


def _canonical_key(key: str) -> str:
    return re.sub(r"[\s_\-]+", "", str(key).strip().lower())


def _match_field(key: str) -> str | None:
    canonical = _canonical_key(key)
    if not canonical or canonical in {":", ":", ""}:
        return "recommendation"
    for field, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            if _canonical_key(alias) == canonical:
                return field
    return None


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = re.search(r"\d+(?:[.,]\d+)?", value.replace(",", "."))
        if match:
            return float(match.group().replace(",", "."))
    return None


def _coerce_int(value: Any) -> int | None:
    number = _coerce_float(value)
    if number is None:
        return None
    return int(round(number))


def _coerce_arguments(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        parts = re.split(r"[\n;]+", value)
        return [part.strip(" -•") for part in parts if part.strip()]
    return []


def _looks_like_recommendation(value: str) -> bool:
    text = value.strip()
    if not text or len(text) > 160:
        return False
    if re.match(r"^(П1|П2|X|1X2|ТБ|ТМ|1|2|Over|Under)", text, re.IGNORECASE):
        return True
    return "—" in text or " - " in text


def normalize_analysis_data(data: dict[str, Any]) -> dict[str, Any]:
    flat = _flatten_dict(data)
    normalized: dict[str, Any] = {}

    for key, value in flat.items():
        field = _match_field(str(key))
        if field and field not in normalized:
            normalized[field] = value

    if not normalized.get("recommendation"):
        for value in flat.values():
            if isinstance(value, str) and _looks_like_recommendation(value):
                normalized["recommendation"] = value.strip()
                break

    if normalized.get("coefficient") is not None:
        normalized["coefficient"] = _coerce_float(normalized["coefficient"])
    if normalized.get("probability_percent") is not None:
        normalized["probability_percent"] = _coerce_int(normalized["probability_percent"])
    if "arguments" in normalized:
        normalized["arguments"] = _coerce_arguments(normalized["arguments"])

    for field in ("risk", "confidence", "market", "explanation"):
        if field in normalized and normalized[field] is not None:
            normalized[field] = str(normalized[field]).strip()

    return normalized


def parse_analysis_result(data: dict[str, Any]) -> AnalysisResult:
    normalized = normalize_analysis_data(data)
    try:
        return AnalysisResult.model_validate(normalized)
    except ValidationError as exc:
        missing = [err["loc"][0] for err in exc.errors() if err["type"] == "missing"]
        raise RuntimeError(
            f"AI synthesis missing fields: {', '.join(str(item) for item in missing)}"
        ) from exc
