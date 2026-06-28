from app.services.ai.providers.nous_client import parse_json_response


def test_parse_json_response_plain():
    data = parse_json_response('{"recommendation": "test"}')
    assert data["recommendation"] == "test"


def test_parse_json_response_codeblock():
    raw = '```json\n{"risk": "medium"}\n```'
    data = parse_json_response(raw)
    assert data["risk"] == "medium"
