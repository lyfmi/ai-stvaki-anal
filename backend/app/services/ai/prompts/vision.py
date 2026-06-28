VISION_SYSTEM_PROMPT = """You are a sports betting screenshot parser.
Extract structured data from the betting screenshot image.
Do NOT make betting recommendations — only extract visible information.
Respond with valid JSON only, no markdown."""

VISION_USER_PROMPT = """Analyze this betting screenshot and return JSON:
{
  "sport": "football|basketball|tennis|hockey|other",
  "league": "league name or null",
  "home_team": "team name",
  "away_team": "team name",
  "match_datetime": "ISO datetime or null",
  "market_type": "1X2|total|handicap|other",
  "available_outcomes": [{"label": "П1|X|П2|...", "coefficient": 1.92}],
  "screenshot_notes": "what is visible or unclear",
  "search_queries": ["query1 in English", "query2 in English"],
  "parse_confidence": "high|medium|low|failed"
}

Rules:
- search_queries: exactly 1-2 short English queries for web search (lineups, injuries, H2H, match status)
- If screenshot is unreadable set parse_confidence to "failed"
- Extract all visible odds/coefficients"""
