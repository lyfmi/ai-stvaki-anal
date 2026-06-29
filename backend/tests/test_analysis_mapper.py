from datetime import datetime
from unittest.mock import MagicMock

from app.services.analysis_mapper import _best_arguments, analysis_to_out


def test_best_arguments_handles_null_raw_arguments():
    row = MagicMock()
    row.arguments = []
    row.raw_ai_response = {"arguments": None}
    assert _best_arguments(row) is None


def test_analysis_to_out_handles_null_raw_arguments():
    row = MagicMock()
    row.id = "00000000-0000-0000-0000-000000000001"
    row.recommendation = "П1"
    row.coefficient = 1.5
    row.probability_percent = 60
    row.risk = "medium"
    row.confidence = "medium"
    row.arguments = []
    row.explanation = "test"
    row.created_at = datetime(2026, 6, 29)
    row.analysis_mode = "pre_match"
    row.match_status_label = "Скоро"
    row.match_datetime_msk = "29.06.2026 20:00 МСК"
    row.is_betting_recommendation = True
    row.source_type = "screenshot"
    row.raw_ai_response = {"arguments": None}

    out = analysis_to_out(row)
    assert out.arguments is None
