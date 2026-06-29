from app.services.ai.providers.json_utils import (
    parse_ai_json,
    parse_json_response,
    _repair_malformed_json,
)


def test_parse_json_response_plain():
    data = parse_json_response('{"recommendation": "test"}')
    assert data["recommendation"] == "test"


def test_parse_json_response_codeblock():
    raw = '```json\n{"risk": "medium"}\n```'
    data = parse_json_response(raw)
    assert data["risk"] == "medium"


def test_repair_malformed_stepfun_json():
    raw = '{",\" :\"test\",\"market\":\"1X2\",\"coefficient\":1.5}'
    repaired = _repair_malformed_json(raw)
    data = parse_json_response(repaired)
    assert data["recommendation"] == "test"
    assert data["market"] == "1X2"
    assert data["coefficient"] == 1.5


def test_parse_json_response_malformed_without_explicit_repair():
    raw = '{",\" :\"П1 — Arsenal\",\"market\":\"1X2\",\"risk\":\"medium\"}'
    data = parse_json_response(raw)
    assert "П1" in data["recommendation"]


def test_parse_ai_json_prefers_content():
    content = '{"recommendation": "from content"}'
    reasoning = '{"recommendation": "from reasoning"}'
    data = parse_ai_json(content, reasoning)
    assert data["recommendation"] == "from content"


def test_parse_ai_json_falls_back_to_reasoning():
    content = "not json at all"
    reasoning = 'Some text before {"recommendation": "from reasoning", "market": "1X2"}'
    data = parse_ai_json(content, reasoning)
    assert data["recommendation"] == "from reasoning"


def test_parse_ai_json_raises_when_both_invalid():
    try:
        parse_ai_json("broken", "also broken")
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert "invalid JSON" in str(exc)
