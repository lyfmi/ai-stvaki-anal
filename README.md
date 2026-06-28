# AI Bet Bot — Backend + Telegram Bot

Telegram betting funnel bot with 3-stage AI analysis:
**Vision (stepfun 3.7 flash) → DuckDuckGo Search → Final LLM synthesis**

## Quick start (local)

```bash
cp .env.example .env
# Edit .env: set AI_MOCK=true for testing without API keys

docker compose up -d --build
curl http://127.0.0.1:8010/health
```

## Stack

- **backend** — FastAPI, PostgreSQL, Redis, Alembic
- **bot-service** — aiogram 3 webhook
- **AI pipeline** — Nous Inference API + free DuckDuckGo search with Redis cache

## Deploy

See [deploy/README-deploy.md](deploy/README-deploy.md)
