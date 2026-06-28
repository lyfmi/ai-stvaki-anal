"""Map AiAnalysis ORM rows to API schemas."""
from app.models import AiAnalysis
from app.schemas import AnalysisDetailOut, AnalysisOut, PremiumInsights


def analysis_to_out(row: AiAnalysis) -> AnalysisOut:
    return AnalysisOut(
        id=row.id,
        recommendation=row.recommendation,
        coefficient=float(row.coefficient) if row.coefficient is not None else None,
        probability_percent=row.probability_percent,
        risk=row.risk,
        confidence=row.confidence,
        arguments=row.arguments,
        explanation=row.explanation,
        created_at=row.created_at,
        analysis_mode=row.analysis_mode,
        match_status_label=row.match_status_label,
        match_datetime_msk=row.match_datetime_msk,
        is_betting_recommendation=row.is_betting_recommendation,
        source_type=row.source_type or "screenshot",
    )


def analysis_to_detail(row: AiAnalysis) -> AnalysisDetailOut:
    premium = None
    if row.premium_payload:
        try:
            premium = PremiumInsights.model_validate(row.premium_payload)
        except Exception:
            premium = None
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
