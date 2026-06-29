"""Map AiAnalysis ORM rows to API schemas."""
from app.models import AiAnalysis
from app.schemas import AnalysisDetailOut, AnalysisOut
from app.services.ai.normalize import coerce_premium_insights


def _is_truncated_argument(text: str) -> bool:
    text = text.strip()
    if len(text) < 20:
        return False
    if text[-1] in ".!?…":
        return False
    last_word = text.split()[-1] if text.split() else ""
    if len(last_word) < 4:
        return True
    return text[-1].isalnum()


def _filter_arguments(args: list[str] | None) -> list[str] | None:
    if not args:
        return None
    cleaned = [a for a in args if a.strip() and not _is_truncated_argument(a)]
    return cleaned or None


def _best_arguments(row: AiAnalysis) -> list[str] | None:
    stored = _filter_arguments(row.arguments or []) or []
    raw = (row.raw_ai_response or {}).get("arguments") if row.raw_ai_response else None
    raw_list = (
        _filter_arguments([str(a) for a in raw if str(a).strip()]) if isinstance(raw, list) else None
    ) or []
    if len(raw_list) > len(stored):
        return raw_list
    return stored or None


def _best_premium(row: AiAnalysis):
    premium = coerce_premium_insights(row.premium_payload)
    if premium is not None:
        return premium
    if row.raw_ai_response:
        return coerce_premium_insights(row.raw_ai_response.get("premium_insights"))
    return None


def _result_meta(row: AiAnalysis) -> tuple[str | None, str | None]:
    raw = row.raw_ai_response or {}
    return raw.get("final_score"), raw.get("winner")


def analysis_to_out(row: AiAnalysis) -> AnalysisOut:
    final_score, winner = _result_meta(row)
    return AnalysisOut(
        id=row.id,
        recommendation=row.recommendation,
        coefficient=float(row.coefficient) if row.coefficient is not None else None,
        probability_percent=row.probability_percent,
        risk=row.risk,
        confidence=row.confidence,
        arguments=_best_arguments(row),
        explanation=row.explanation,
        created_at=row.created_at,
        analysis_mode=row.analysis_mode,
        match_status_label=row.match_status_label,
        match_datetime_msk=row.match_datetime_msk,
        is_betting_recommendation=row.is_betting_recommendation,
        source_type=row.source_type or "screenshot",
        final_score=final_score,
        winner=winner,
    )


def analysis_to_detail(row: AiAnalysis) -> AnalysisDetailOut:
    premium = _best_premium(row)

    base = analysis_to_out(row)
    return AnalysisDetailOut(
        **base.model_dump(),
        vision_payload=row.vision_payload,
        search_payload=row.search_payload,
        pipeline_version=row.pipeline_version,
        latency_ms=row.latency_ms,
        premium_insights=premium,
    )


def persist_analysis_fields(analysis: AiAnalysis, result) -> None:
    """Apply AnalysisResult fields onto AiAnalysis row."""
    analysis.recommendation = result.recommendation
    analysis.coefficient = result.coefficient
    analysis.probability_percent = result.probability_percent
    analysis.explanation = result.explanation
    analysis.risk = result.risk
    analysis.confidence = result.confidence
    analysis.arguments = result.arguments
    analysis.analysis_mode = result.analysis_mode
    analysis.match_status_label = result.match_status_label
    analysis.match_datetime_msk = result.match_datetime_msk
    analysis.is_betting_recommendation = result.is_betting_recommendation
    analysis.raw_ai_response = result.model_dump()
    if result.premium_insights:
        analysis.premium_payload = result.premium_insights.model_dump()
    else:
        coerced = coerce_premium_insights(result.model_dump().get("premium_insights"))
        if coerced:
            analysis.premium_payload = coerced.model_dump()
