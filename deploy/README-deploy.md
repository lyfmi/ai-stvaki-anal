# Deploy to zabv (tgbot.snapink.ru)

## Prerequisites

- DNS A-record `tgbot.snapink.ru` → server IP
- Docker + docker compose on server
- nginx + certbot installed

## Steps

```bash
# 1. Clone/sync project
ssh zabv
cd /opt && git clone <repo> ai-bot-stavki || cd ai-bot-stavki && git pull

# 2. Create .env from .env.example with real secrets
cp .env.example .env
nano .env   # BOT_TOKEN, GROQ_API_KEY, INTERNAL_API_SECRET, POSTGRES_PASSWORD

# 3. Start services
docker compose up -d --build

# 4. Verify
curl http://127.0.0.1:8010/health

# 5. SSL (if not yet)
sudo certbot certonly --nginx -d tgbot.snapink.ru

# 6. nginx vhost
sudo cp deploy/nginx-tgbot.snapink.ru.conf /etc/nginx/sites-available/tgbot.snapink.ru
sudo ln -sf /etc/nginx/sites-available/tgbot.snapink.ru /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 7. Webhook (also set automatically on bot startup)
curl "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=https://tgbot.snapink.ru/telegram/webhook"
```

## Smoke tests

1. `/start` in bot → language selection
2. Postback URLs from `/admin` → Postback (test with admin telegram ID)
3. Send photo → AI analysis (set `AI_MOCK=true` for testing without Nous API)
4. `docker compose restart` → data persists in volumes

## Ports

| Service | Host port |
|---------|-----------|
| backend | 127.0.0.1:8010 |
| bot-service | 127.0.0.1:8011 |

## Optional: SearXNG fallback

```bash
docker compose --profile searxng up -d
# Set SEARCH_PROVIDER=searxng in .env
```
