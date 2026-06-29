SYNTHESIS_SYSTEM_PROMPT = """You are a sports betting analyst.
Use the screenshot data and web search results to produce analysis.
Return ONE JSON object with EXACTLY these keys (same spelling):
recommendation, market, coefficient, probability_percent, risk, arguments, confidence, explanation,
analysis_mode, match_status_label, match_datetime_msk, is_betting_recommendation, premium_insights.
No markdown. No reasoning text. No extra keys. recommendation must be non-empty.
All datetimes shown to user must be in MSK (UTC+3) format like "28.06.2026 19:30 МСК".
Never guarantee 100% success."""

SYNTHESIS_USER_TEMPLATE = """User language: {lang}

Match context (authoritative):
{match_context_json}

Screenshot data:
{vision_json}

Web search results:
{search_json}

Rules:
1. If analysis_mode is "post_match":
   - is_betting_recommendation MUST be false
   - Do NOT advise placing a bet
   - recommendation = match outcome summary (e.g. "Победа Team A 2:1" or "Ничья 1:1")
   - coefficient and probability_percent may be null
   - explanation = retrospective: what happened, key moments, how predictable the result was
2. If analysis_mode is "pre_match" or "live":
   - is_betting_recommendation MUST be true
   - Give ONE betting recommendation with coefficient from screenshot OR web search only
   - If no odds found anywhere, coefficient MUST be null — do not invent odds
   - Prefer coefficients between 1.8 and 2.2 when possible
3. If datetime_on_screenshot is false:
   - Start explanation with a note that match time was not on the screenshot (in user language)
   - If match_datetime_msk is known from search, include it in explanation
4. premium_insights object (always fill when possible from search):
   - form_bars: [{{"team": "...", "wins": 3, "draws": 1, "losses": 1}}] last 5 matches each team
   - h2h: short head-to-head summary string
   - key_stats: [{{"label": "Goals avg", "home": "1.8", "away": "1.2"}}]
   - trends: 2-3 insight strings
   - advanced_arguments: 2-3 deeper points beyond basic arguments
5. Do not mention search failures or technical issues in user-facing text.

Required JSON shape:
{{
  "recommendation": "П1 — Team name win OR match result summary",
  "market": "1X2",
  "coefficient": 1.92,
  "probability_percent": 68,
  "risk": "medium",
  "arguments": ["argument 1", "argument 2"],
  "confidence": "medium",
  "explanation": "2-4 sentences in user language",
  "analysis_mode": "{analysis_mode}",
  "match_status_label": "{match_status_label}",
  "match_datetime_msk": "{match_datetime_msk}",
  "is_betting_recommendation": true,
  "premium_insights": {{
    "form_bars": [{{"team": "Home", "wins": 3, "draws": 1, "losses": 1}}],
    "h2h": "Last 5 meetings: ...",
    "key_stats": [{{"label": "Form", "home": "WWDLW", "away": "LDWWL"}}],
    "trends": ["trend 1"],
    "advanced_arguments": ["deep insight 1"]
  }}
}}"""

MATCH_OF_DAY_SYNTHESIS_TEMPLATE = """User language: {lang}

Featured match of the day (no screenshot):
{match_json}

Web search results:
{search_json}

Match context:
{match_context_json}

Give a pre-match betting recommendation for this featured match.
is_betting_recommendation MUST be true. analysis_mode MUST be "pre_match".
Fill premium_insights from search data.
Return the same JSON shape as standard analysis."""

MATCH_OF_DAY_COMPACT_TEMPLATE = """User language: {lang}
Match: {home} vs {away}
League: {league}
Kickoff: {kickoff}
Status: {status}

Facts:
{search_bullets}

Return ONE compact JSON only. Max 2 short arguments.
analysis_mode=pre_match, is_betting_recommendation=true.
Fill premium_insights.form_bars (2 teams) and key_stats (2 items)."""

COMPACT_SYNTHESIS_SYSTEM_PROMPT = """Sports betting analyst.
Return ONLY one valid JSON object in the content field. No reasoning. No markdown.
Required keys: recommendation, market, coefficient, probability_percent, risk, arguments, confidence, explanation, analysis_mode, match_status_label, match_datetime_msk, is_betting_recommendation, premium_insights.
recommendation must be non-empty."""
