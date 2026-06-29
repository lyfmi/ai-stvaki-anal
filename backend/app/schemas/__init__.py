from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UserOut(BaseModel):
    id: UUID
    telegram_id: int
    username: str | None
    language: str
    funnel_state: str
    is_channel_subscribed: bool
    is_registered: bool
    is_deposited: bool
    has_unlimited: bool
    is_admin: bool = False
    attempts_count: int
    attempts_window_start: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserStatusOut(BaseModel):
    user: UserOut
    can_analyze: bool
    attempts_remaining: int
    attempts_reset_at: datetime | None
    daily_limit: int


class LanguageUpdate(BaseModel):
    language: str = Field(min_length=2, max_length=5)


class AnalysisOutcome(BaseModel):
    label: str
    coefficient: float | None = None


class VisionPayload(BaseModel):
    sport: str | None = None
    league: str | None = None
    home_team: str | None = None
    away_team: str | None = None
    match_datetime: str | None = None
    market_type: str | None = None
    available_outcomes: list[AnalysisOutcome] = Field(default_factory=list)
    screenshot_notes: str | None = None
    search_queries: list[str] = Field(default_factory=list)
    parse_confidence: str = "high"
    datetime_on_screenshot: bool = False
    odds_on_screenshot: bool = False
    match_status_hint: str = "unknown"


class SearchResultItem(BaseModel):
    query: str
    title: str
    snippet: str
    url: str = ""


class SearchPayload(BaseModel):
    queries_executed: list[str] = Field(default_factory=list)
    results: list[SearchResultItem] = Field(default_factory=list)
    search_status: str = "ok"


class FormBarItem(BaseModel):
    team: str
    wins: int = 0
    draws: int = 0
    losses: int = 0


class KeyStatItem(BaseModel):
    label: str
    home: str
    away: str


class PremiumInsights(BaseModel):
    form_bars: list[FormBarItem] = Field(default_factory=list)
    h2h: str = ""
    key_stats: list[KeyStatItem] = Field(default_factory=list)
    trends: list[str] = Field(default_factory=list)
    advanced_arguments: list[str] = Field(default_factory=list)


class MatchContextOut(BaseModel):
    analysis_mode: str = "pre_match"
    match_status_label: str = ""
    match_datetime_msk: str | None = None


class AnalysisResult(BaseModel):
    recommendation: str
    market: str | None = None
    coefficient: float | None = None
    probability_percent: int | None = None
    risk: str = "medium"
    arguments: list[str] = Field(default_factory=list)
    confidence: str = "medium"
    explanation: str = ""
    analysis_mode: str = "pre_match"
    match_status_label: str = ""
    match_datetime_msk: str | None = None
    is_betting_recommendation: bool = True
    premium_insights: PremiumInsights | None = None


class AnalysisOut(BaseModel):
    id: UUID
    recommendation: str | None
    coefficient: float | None
    probability_percent: int | None
    risk: str | None
    confidence: str | None
    arguments: list[str] | None
    explanation: str | None
    created_at: datetime
    analysis_mode: str | None = None
    match_status_label: str | None = None
    match_datetime_msk: str | None = None
    is_betting_recommendation: bool | None = True
    source_type: str | None = "screenshot"

    model_config = {"from_attributes": True}


class AnalysisDetailOut(AnalysisOut):
    vision_payload: dict | None = None
    search_payload: dict | None = None
    pipeline_version: str | None = None
    latency_ms: dict | None = None
    premium_insights: PremiumInsights | None = None


class MatchOfDayOut(BaseModel):
    home_team: str
    away_team: str
    league: str
    kickoff_msk: str
    kickoff_at: str | None = None
    teaser: str
    cached: bool = False
    is_live: bool = False


class AdminStatsOut(BaseModel):
    total_users: int
    registered_users: int
    deposited_users: int
    unlimited_users: int
    total_analyses: int
    analyses_today: int


class AdminOut(BaseModel):
    telegram_id: int
    username: str | None = None
    removable: bool
    source: str


class AdminAdd(BaseModel):
    telegram_id: int | None = None
    username: str | None = None


class AdminRemove(BaseModel):
    telegram_id: int


class SettingsUpdate(BaseModel):
    affiliate_ref_url: str | None = None
    affiliate_promo_code: str | None = None
    channel_id: str | None = None
    channel_url: str | None = None
    reports_chat_id: str | None = None
    support_url: str | None = None
    unlimited_enabled: bool | None = None
    unlimited_price_amount: int | None = None
    unlimited_price_currency: str | None = None
    tribute_enabled: bool | None = None
    tribute_api_key: str | None = None
    tribute_shop_id: str | None = None
    tribute_webhook_secret: str | None = None
    tribute_mode: str | None = None
    tribute_product_link: str | None = None
    daily_attempts_limit: int | None = None


class AffiliateUpdate(BaseModel):
    ref_url: str
    promo_code: str


class UnlimitedGrant(BaseModel):
    telegram_id: int


class BroadcastCreate(BaseModel):
    text: str
    photo_url: str | None = None


class NotifyRequest(BaseModel):
    telegram_id: int
    template: str
    params: dict = Field(default_factory=dict)


class PaymentCreateOut(BaseModel):
    order_uuid: str
    webapp_payment_url: str | None = None
    payment_url: str | None = None
    amount: int
    currency: str


class AuthTelegramRequest(BaseModel):
    init_data: str


class AuthTelegramResponse(BaseModel):
    token: str
    user: UserOut
