SYNTHESIS_SYSTEM_PROMPT = """You are a sports betting analyst.
Use the screenshot data and web search results to recommend ONE outcome.
Output compact valid JSON only. No markdown, no reasoning text.
Never guarantee 100% success. Prefer coefficients between 1.8 and 2.2 when possible."""

SYNTHESIS_USER_TEMPLATE = """User language: {lang}

Screenshot data:
{vision_json}

Web search results:
{search_json}

Return JSON:
{{
  "recommendation": "П1 — Team name win",
  "market": "1X2",
  "coefficient": 1.92,
  "probability_percent": 68,
  "risk": "low|medium|high",
  "arguments": ["argument 1", "argument 2"],
  "confidence": "low|medium|high",
  "explanation": "2-4 sentences in user language"
}}

If search failed, lower confidence and mention limited data in explanation."""
