from app.schemas import SearchPayload, SearchResultItem, VisionPayload
from app.services.ai.odds_resolver import (
    apply_odds_policy,
    coefficient_from_vision,
    extract_1win_odds_from_search,
)
from app.services.ai.image_prepare import prepare_vision_image
from app.schemas import AnalysisResult


def test_coefficient_from_vision_brazil_japan_odds():
    vision = VisionPayload(
        home_team="Brazil",
        away_team="Japan",
        odds_on_screenshot=True,
        available_outcomes=[
            {"label": "1", "coefficient": 1.74},
            {"label": "X", "coefficient": 3.71},
            {"label": "2", "coefficient": 5.2},
        ],
    )
    coef = coefficient_from_vision(vision, "П1 — Победа Brazil")
    assert coef == 1.74


def test_apply_odds_policy_clears_invented_without_1win():
    result = AnalysisResult(
        recommendation="П1 — Победа Brazil",
        coefficient=1.65,
        probability_percent=60,
        analysis_mode="pre_match",
        is_betting_recommendation=True,
    )
    search = SearchPayload(
        results=[
            SearchResultItem(
                query="q",
                title="Preview",
                snippet="Brazil favored in betting markets",
                url="https://example.com",
            )
        ]
    )
    out = apply_odds_policy(result, search=search, home="Brazil", away="Japan")
    assert out.coefficient is None
    assert out.probability_percent is None


def test_extract_1win_odds_from_search_snippet():
    search = SearchPayload(
        results=[
            SearchResultItem(
                query="q",
                title="1win odds",
                snippet="Brazil vs Japan 1win 1.74 3.71 5.20",
                url="https://1win.com",
            )
        ]
    )
    odds = extract_1win_odds_from_search(search, "Brazil", "Japan")
    assert odds is not None
    assert odds["home"] == 1.74
    assert odds["draw"] == 3.71


def test_prepare_vision_image_upscales_small_crop():
    from PIL import Image
    import io

    img = Image.new("RGB", (200, 400), color=(30, 30, 30))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    out, mime = prepare_vision_image(buf.getvalue())
    assert mime == "image/jpeg"
    with Image.open(io.BytesIO(out)) as prepared:
        assert max(prepared.size) >= 1024
