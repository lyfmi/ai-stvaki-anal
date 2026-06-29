import json
import re


def _strip_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    return cleaned.strip()


def _repair_malformed_json(text: str) -> str:
    repaired = text.strip()
    repaired = re.sub(
        r'^\{\s*",\s*"\s*:',
        '{"recommendation":',
        repaired,
    )
    repaired = re.sub(
        r'^\{\s*\\",\\"\s*:',
        '{"recommendation":',
        repaired,
    )
    return repaired


def _json_candidates(text: str) -> list[str]:
    cleaned = _strip_fences(text)
    candidates = [_repair_malformed_json(cleaned)]

    start = 0
    while True:
        start = cleaned.find("{", start)
        if start == -1:
            break
        depth = 0
        for index, char in enumerate(cleaned[start:], start):
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    fragment = cleaned[start : index + 1]
                    candidates.append(_repair_malformed_json(fragment))
                    candidates.append(fragment)
                    break
        start += 1

    candidates.append(cleaned)

    unique: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate and candidate not in seen:
            seen.add(candidate)
            unique.append(candidate)
    return unique


def parse_json_response(raw: str | None) -> dict:
    if not raw or not raw.strip():
        raise RuntimeError("Empty AI response")

    for candidate in _json_candidates(raw):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        for candidate in (match.group(), _repair_malformed_json(match.group())):
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

    raise RuntimeError("AI returned invalid JSON")


def parse_ai_json(content: str | None, reasoning: str | None = None) -> dict:
    last_error: RuntimeError | None = None
    for source in (content, reasoning):
        if not source:
            continue
        try:
            return parse_json_response(source)
        except RuntimeError as exc:
            last_error = exc
    raise last_error or RuntimeError("AI returned invalid JSON")
