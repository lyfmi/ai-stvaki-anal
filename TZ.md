# Техническое задание: AI Анализ Ставок (Telegram Bot + Web App)

> Версия: 1.0  
> Дата: 2026-06-28  
> Источники: `research/01_video_youtube_transcription.txt`, `research/02_video_langsignalbot421_transcription.txt`, `research/03_website_parsed_content.md`

---

## 1. Цель продукта

Разработать Telegram-бота для беттинг-воронки с **AI-анализом спортивных событий по скриншоту**.

**Ключевые принципы:**
- **Основной интерфейс** — Telegram Web App (React)
- **Telegram Bot** — inline-кнопки, навигация, уведомления, админ-команды
- **Функционал** максимально близок к конкуренту (GrayScheme «AI Анализ Ставок»)
- **Установка** проще: `docker compose up`, без Windows, лицензий и активации по ID машины
- **Модель продажи** — бессрочная (без ограничения 30 дней), в отличие от аренды конкурента

### Что повторяем у конкурента

| Функция | Описание |
|---------|----------|
| Воронка | Язык → подписка на канал → регистрация в партнёрке → первый депозит → AI-анализ |
| AI-анализ | Скриншот БК → рекомендация + вероятность + объяснение |
| Лимиты | 10 попыток / 24 часа |
| Безлимит | Опциональная покупка через **Tribute** + ручная выдача админом (fallback) |
| Партнёрка | Postback регистрации и первого депозита |
| Админка | Рассылка, смена реф. ссылки, статистика, безлимит |
| Языки | 11+ языков, настраиваемый список |
| Web App | Дашборд попыток, загрузка скрина, статусы |

### Что сознательно НЕ делаем

- Активация по ID машины / @GraySchemebot
- Ограничение жизни бота 30 днями (аренда)
- Зависимость от Windows / `start.cmd`
- Отдельный «Бот Б» через Telegram API sendMessage (заменяем HTTP postback webhook)
- Ручная активация Web App у стороннего админа
- SQLite + `user.db` на файловой системе Windows

---

## 2. Бизнес-модель и отличия от конкурента

### Конкурент (GrayScheme)

- Аренда: **40$/мес** или **160$/год**
- Лицензия привязана к машине
- Web App активирует их админ
- Postback через второй бот + канал «Отчёты»
- Сложная установка: Windows Server, YAML-конфиги, 2 бота, 2 канала

### Наш продукт

- **Продажа на безлимитное время** — покупатель получает полную версию без истечения срока
- **Docker-установка** — один `docker compose up -d` после заполнения `.env`
- **Admin UI** в Web App — настройка партнёрки, языков, рассылок без редактирования YAML
- **HTTP Postback** — прямой webhook в backend, без промежуточного Telegram-канала (опционально сохранить канал для логов)
- **Единый бот** — один токен @BotFather, без «Бот Б»

> Лимит **10 попыток/24ч** и **безлимит для конечных пользователей бота** — это часть воронки, не лицензирование. Они остаются как у конкурента.

---

## 3. Стек технологий

| Слой | Технология |
|------|------------|
| Frontend (Web App) | **React** + TypeScript, Telegram WebApp SDK |
| Backend | **FastAPI** (REST API, webhooks, admin API) |
| Bot Service | **Python** (aiogram 3.x) — отдельный Docker-контейнер |
| База данных | **PostgreSQL 16+** |
| Кэш / rate limit | **Redis** (рекомендуется) |
| Миграции | **Alembic** |
| AI | OpenAI Vision / Claude / Gemini (настраивается через `.env`) |
| Reverse proxy | **Nginx** или **Traefik** |
| Оркестрация | **Docker Compose** |
| Хранение файлов | Docker volume `storage_data` (скрины, бэкапы, логи) |
| Бэкапы БД | Cron-контейнер или pg_dump в volume по расписанию |
| Платёжная система | **[Tribute](https://wiki.tribute.tg/ru/for-shops)** — Shop API + вебхуки (карты, СБП, Telegram Stars, TON) |

---

## 4. Архитектура системы

```
┌─────────────────────────────────────────────────────────────────┐
│                         Docker Compose                          │
├─────────────┬─────────────┬──────────────┬───────────┬────────────┤
│   nginx     │  frontend   │   backend    │ bot-svc   │  worker    │
│  (proxy)    │   (React)   │  (FastAPI)   │ (aiogram) │ (optional) │
├─────────────┴─────────────┴──────┬───────┴───────────┴────────────┤
│                                  │                               │
│         postgres ◄───────────────┤                               │
│         redis  ◄─────────────────┘                               │
│         volumes: pg_data, storage_data, backup_data              │
└─────────────────────────────────────────────────────────────────┘
         ▲                    ▲                    ▲
         │                    │                    │
    Telegram User      Partner Program        Admin Browser
    (Bot + WebApp)     (Postback HTTP)        (Web App / Bot)
```

### Разделение ответственности

| Сервис | Задачи |
|--------|--------|
| **bot-service** | `/start`, inline-кнопки, проверка подписки, открытие Web App, админ-команды, рассылки |
| **backend** | Бизнес-логика, REST API, postback webhooks, AI-анализ, лимиты, БД |
| **frontend** | Web App UI: дашборд, загрузка скрина, история, статусы, admin panel |
| **worker** | Фоновые задачи: рассылки, AI-очередь, бэкапы (опционально на MVP) |

### Потоки данных

1. **Пользователь** → Bot (inline) → Web App → Backend REST API
2. **Партнёрка** → `POST /api/webhook/postback/*` → Backend → обновление статуса user
3. **Admin** → Bot `/admin` или Web App Admin → Backend
4. **Tribute** → `POST /api/webhook/tribute` → Backend → auto-grant безлимита
5. **Bot-service** ↔ Backend — внутренний REST или shared DB (предпочтительно REST)

---

## 5. Пользовательская воронка (State Machine)

### Состояния пользователя (`user.funnel_state`)

```
NEW
  → LANGUAGE_SELECTED
  → CHANNEL_SUBSCRIBED
  → REGISTRATION_PENDING
  → REGISTERED
  → DEPOSIT_PENDING
  → DEPOSIT_CONFIRMED
  → ACTIVE          (доступ к AI-анализу)
  → LIMIT_EXCEEDED  (10/24ч исчерпаны, без безлимита)
  → UNLIMITED       (безлимит активен)
```

### Пошаговый сценарий

```
Instagram / YouTube / Reels
        ↓
   /start в Telegram Bot
        ↓
┌───────────────────┐
│ Выбор языка       │  inline-кнопки с флагами (ru, en, hi, es...)
└─────────┬─────────┘
          ↓
┌───────────────────┐
│ Подписка на канал │  [Подписаться] [✓ Проверить]
└─────────┬─────────┘
          ↓
┌───────────────────┐
│ Получить сигнал   │  → Web App или inline-шаги
└─────────┬─────────┘
          ↓
┌───────────────────┐
│ Регистрация       │  кнопка → партнёрская ссылка + промокод
└─────────┬─────────┘  postback → REGISTERED
          ↓
┌───────────────────┐
│ Первый депозит    │  инструкция + ссылка в БК
└─────────┬─────────┘  postback → DEPOSIT_CONFIRMED
          ↓
┌───────────────────┐
│ AI Анализ         │  Web App: загрузка скрина
│ 10 попыток / 24ч  │  → recommendation + probability + explanation
└─────────┬─────────┘
          ↓ (лимит исчерпан)
┌───────────────────┐
│ Ждать 24ч         │  или [Купить безлимит] → Tribute → auto-grant
└───────────────────┘
```

### Inline-кнопки бота (основные)

| Экран | Кнопки |
|-------|--------|
| Старт | Языки (grid inline) |
| Подписка | `Подписаться на канал` (url), `Проверить подписку` (callback) |
| Воронка | `Получить сигнал`, `Открыть приложение` (web_app), `Поддержка` (url) |
| Регистрация | `Зарегистрироваться` (url → ref link), `Я зарегистрировался` (callback → polling статуса) |
| Депозит | `Пополнить` (url), `Проверить депозит` (callback) |
| Лимит | `Открыть приложение`, `Купить безлимит` (Tribute), `Поддержка` |
| Admin | `📊 Статистика`, `📢 Рассылка`, `🔗 Реф. ссылка`, `♾ Безлимит`, `⚙ Настройки` |

> После прохождения воронки основная работа идёт через **Web App**. Bot остаётся для уведомлений, быстрого доступа и админки.

---

## 6. Telegram Web App (основной интерфейс)

### Экраны пользователя

| Экран | Содержимое |
|-------|------------|
| **Dashboard** | Статус доступа, оставшиеся попытки / ∞, кнопка «Анализировать» |
| **Upload** | Drag & drop / camera — загрузка скриншота БК |
| **Result** | Исход, коэффициент, вероятность %, объяснение |
| **History** | Список прошлых анализов с превью |
| **Profile** | Язык, статус подписки/регистрации/депозита |
| **Unlimited** | Цена, кнопка «Купить безлимит» → оплата через Tribute |
| **Support** | Ссылка на Telegram поддержки |

### Экраны админа (в том же Web App, role=admin)

| Экран | Содержимое |
|-------|------------|
| **Stats** | Users, registrations, deposits, analyses, conversions |
| **Broadcast** | Текст + медиа → отправка всем |
| **Affiliate** | Реф. ссылка, промокод, postback URLs (copy) |
| **Unlimited** | Выдать/забрать по Telegram ID |
| **Languages** | Включённые языки, default language |
| **Settings** | Лимиты, Tribute (цена/валюта), канал, support URL |

### Интеграция с Telegram

- Авторизация через `Telegram.WebApp.initData` → backend валидирует HMAC
- `MainButton` для основных действий (отправить скрин, сохранить)
- Theme params из Telegram для нативного вида
- Deep link: `t.me/BotName/app` → сразу Web App

---

## 7. Партнёрская программа и Postback

### 7.1. Настройка партнёрки (Admin)

Админ задаёт в Web App / `.env`:

| Параметр | Пример | Описание |
|----------|--------|----------|
| `affiliate_ref_url` | `https://1win.com/...` | Реферальная ссылка |
| `affiliate_promo_code` | `AIBET776` | Промокод (показывается в боте/Web App) |
| `affiliate_sub_param` | `sub1` | Имя параметра для Telegram ID в postback |

**Как добавить ссылку (упрощённо vs конкурент):**

1. Зарегистрироваться в партнёрке (OneWin, Melbet и т.д.)
2. Создать источник трафика и реф. ссылку
3. Создать промокод
4. В Admin UI вставить ссылку и промокод — **сохраняется в `app_settings`**
5. Backend автоматически генерирует postback URL для копирования в партнёрку

> У конкурента: `/admin4` → ввод ссылки вручную + правка `lang.yaml` для промокода.  
> У нас: одна форма в Admin UI, промокод подставляется во все переводы автоматически.

### 7.2. Передача Telegram ID в партнёрку

При переходе пользователя по реф. ссылке backend формирует URL:

```
{affiliate_ref_url}?{sub_param}={telegram_user_id}
```

Партнёрка при регистрации/депозите шлёт postback с этим ID.

### 7.3. Postback endpoints (наш backend)

**Регистрация:**
```
POST /api/webhook/postback/registration
GET  /api/webhook/postback/registration?sub1={telegram_id}   # совместимость
```

**Первый депозит:**
```
POST /api/webhook/postback/deposit
GET  /api/webhook/postback/deposit?sub1={telegram_id}&amount={sum}
```

**Формат legacy (совместимость с OneWin/GrayScheme):**

Партнёрка может слать через свой шаблон. Admin UI показывает готовые URL:

```
# Регистрация
https://your-domain.com/api/webhook/postback/registration?sub1={sub1}

# Первый депозит  
https://your-domain.com/api/webhook/postback/deposit?sub1={sub1}&amount={amount}
```

> У конкурента postback шёл через `api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHANNEL}&text={sub1}|Firstdep|{amount}` и бот парсил канал.  
> У нас — **прямой HTTP webhook**, надёжнее и проще в Docker.

### 7.4. Обработка postback (backend logic)

```python
# Псевдокод
def handle_registration(telegram_id: int):
    user = get_or_create_user(telegram_id)
    user.is_registered = True
    user.funnel_state = "REGISTERED"
    user.registered_at = now()
    notify_user_bot(telegram_id, "registration_confirmed")
    notify_admin(f"User {telegram_id} registered")

def handle_deposit(telegram_id: int, amount: decimal):
    user = get_user(telegram_id)
    if not user.is_registered:
        return  # ignore or log
    user.is_deposited = True
    user.deposit_amount = amount
    user.funnel_state = "DEPOSIT_CONFIRMED"
    user.deposited_at = now()
    notify_user_bot(telegram_id, "deposit_confirmed")
    notify_admin(f"User {telegram_id} deposited {amount}")
    # Открыть доступ к AI
```

### 7.5. Переменные postback в разных партнёрках

| Партнёрка | ID пользователя | Сумма депозита |
|-----------|-----------------|----------------|
| OneWin | `{sub1}` | `{amount}` |
| Другие | `{sub1}` / `{click_id}` / `{player_id}` | `{amount}` / `{sum}` / `{deposit}` |

Admin UI: поле **«Шаблон переменной суммы»** для маппинга. Backend принимает query params гибко.

### 7.6. Тестирование postback (для админа)

Без `{}` в URL — как у конкурента:

```
# Имитация регистрации
https://your-domain.com/api/webhook/postback/registration?sub1=YOUR_TELEGRAM_ID

# Имитация депозита
https://your-domain.com/api/webhook/postback/deposit?sub1=YOUR_TELEGRAM_ID&amount=777
```

Admin может пройти всю воронку без реальной регистрации.

### 7.7. Опционально: Telegram-канал «Отчёты»

Для привычки арбитражников и дублирования логов:
- Backend при postback **дополнительно** шлёт сообщение в приватный канал через Bot API
- Не обязательно для работы системы

---

## 8. AI-анализ скриншота

### Вход
- Изображение (JPEG/PNG/WebP), max 10 MB
- Источник: Web App upload или отправка фото в bot → прокси в backend

### Выход (стабильный JSON)

```json
{
  "recommendation": "П1 — Победа команды А",
  "market": "1X2",
  "coefficient": 1.92,
  "probability_percent": 68,
  "explanation": "Краткое обоснование на языке пользователя",
  "confidence": "medium"
}
```

### Бизнес-правила (как у конкурента)

- Коэффициент обычно в диапазоне **1.8 – 2.2**
- Ответ на языке пользователя
- Время ответа: **≤ 15 сек** (target ≤ 5 сек)
- AI **не гарантирует** 100% — это отражается в UI
- Каждый анализ = **1 попытка** (если нет безлимита)

### Prompt-стратегия

- Vision-модель получает скрин + system prompt
- Извлекает: команды, рынки, коэффициенты
- Выбирает «рекомендуемый» исход с обоснованием
- Fallback при нечитаемом скрине: понятная ошибка пользователю

---

## 9. Лимиты и безлимит

### Бесплатный тариф
- **10 анализов за rolling 24 часа** (Redis или PostgreSQL)
- Сброс: `attempts_reset_at = last_attempt_at + 24h`
- При исчерпании: Web App показывает таймер до сброса

### Безлимит (оплата через Tribute)
- Включается в `app_settings.unlimited_enabled`
- Цена и валюта настраиваются админом
- **Основной flow (автоматический):**
  1. Пользователь жмёт «Купить безлимит» в Web App или inline-кнопку в боте
  2. Backend создаёт заказ в Tribute Shop API (`POST /api/v1/shop/orders`)
  3. Пользователю открывается `webappPaymentUrl` (внутри Telegram) или `paymentUrl` (браузер)
  4. После оплаты Tribute шлёт webhook → backend **автоматически** выдаёт безлимит
  5. Bot/Web App уведомляет: «Безлимит активирован»
- `user.has_unlimited = true` — лимиты не применяются
- **Fallback:** админ вручную выдаёт/забирает безлимит (как у конкурента)

### Admin: grant/revoke (ручной режим)

```
POST /api/admin/unlimited/grant   { "telegram_id": 123456789 }
POST /api/admin/unlimited/revoke  { "telegram_id": 123456789 }
```

Также через inline admin menu в боте: переслать сообщение пользователя или ввести ID.

---

## 9.1. Платёжная система Tribute

> Документация: [API Магазина](https://wiki.tribute.tg/ru/for-shops/api-magazina), [Методы](https://wiki.tribute.tg/ru/for-shops/api-magazina/metody), [Вебхуки](https://wiki.tribute.tg/ru/for-shops/api-magazina/vebkhuki), [Models](https://wiki.tribute.tg/ru/for-shops/api-magazina/models), [Интеграция цифровых товаров](https://wiki.tribute.tg/ru/for-content-creators/digital-product/integrating-digital-products-into-your-product)

### Назначение

Tribute — основная платёжная система для:
- **покупки безлимита** конечными пользователями бота (разовый платёж);
- приём оплаты картами, СБП, Telegram Stars, Wallet Pay (TON);
- автоматической выдачи доступа по webhook без ручного подтверждения админом.

> У конкурента оплата безлимита — ссылка на диалог с админом (Telegram Business) + ручная выдача.  
> У нас — **Tribute + автоматический grant** по webhook.

### Два режима интеграции

| Режим | Когда использовать | Сложность |
|-------|-------------------|-----------|
| **Shop API** (рекомендуется) | Динамическая цена из Admin UI, привязка к `telegram_id` через `customerId` | Средняя |
| **Цифровой товар** (статическая ссылка) | Фиксированная цена, один товар в дашборде Tribute | Простая |

**MVP:** Shop API. Цифровой товар — запасной вариант для быстрого старта без API.

---

### 9.1.1. Настройка Tribute (один раз)

1. Зарегистрироваться в [@tribute](https://t.me/tribute) → Дашборд автора
2. Сгенерировать **API-ключ**: Настройки (⋯) → «Управление API-ключами» → «Сгенерировать API-ключ»
3. Указать **URL вебхука** в настройках API:
   ```
   https://your-domain.com/api/webhook/tribute
   ```
4. Сохранить в `.env`:
   ```env
   TRIBUTE_API_KEY=...
   TRIBUTE_SHOP_ID=...          # опционально, если несколько магазинов
   TRIBUTE_WEBHOOK_SECRET=...   # тот же API-ключ для проверки подписи
   ```

**Авторизация API:** заголовок `Api-Key` в каждом запросе к `https://tribute.tg/api/v1`.

```bash
curl -X GET 'https://tribute.tg/api/v1/shops' \
  -H 'Api-Key: your_api_key_here'
```

---

### 9.1.2. Shop API — создание заказа на безлимит (основной flow)

**Endpoint:** `POST https://tribute.tg/api/v1/shop/orders`

**Request (пример):**
```json
{
  "title": "AI Анализ Ставок — Безлимит",
  "description": "Безлимитный доступ к AI-анализу спортивных событий",
  "amount": 4900,
  "currency": "rub",
  "period": "onetime",
  "customerId": "123456789",
  "successUrl": "https://your-domain.com/payment/success",
  "failUrl": "https://your-domain.com/payment/fail",
  "comment": "unlimited_purchase"
}
```

| Поле | Описание |
|------|----------|
| `amount` | Сумма в **копейках/центах** (4900 = 49.00 RUB) |
| `currency` | `rub`, `usd`, `eur` (нижний регистр) |
| `period` | **`onetime`** — разовая покупка безлимита (не подписка) |
| `customerId` | **Telegram user ID** покупателя (строка, max 256) — ключ для webhook |
| `successUrl` / `failUrl` | Редирект после оплаты (опционально) |

**Response:** объект `ShopOrder` с полями:
- `uuid` — ID заказа (сохраняем в БД)
- `paymentUrl` — оплата в браузере (карта, СБП, TON)
- `webappPaymentUrl` — оплата внутри Telegram WebApp
- `status` — `pending` → `paid` / `failed`

**Backend endpoint (наш):**
```
POST /api/payments/unlimited/create
Response: { "order_uuid", "webapp_payment_url", "payment_url", "amount", "currency" }
```

**UI flow:**
- В Web App: `Telegram.WebApp.openLink(webappPaymentUrl)` или встроенная кнопка
- В боте: inline-кнопка `url=webappPaymentUrl` или `web_app`

### Способы оплаты (Shop API)

| Способ | Условие |
|--------|---------|
| Банковские карты | Всегда |
| СБП | Если включён у продавца; только `period: onetime` |
| Wallet Pay (TON) | Всегда |
| Telegram Stars | При `starsAmount > 0` |

---

### 9.1.3. Webhooks Tribute

**URL:** `POST /api/webhook/tribute`  
**Настройка:** Панель автора → Настройки → API-ключи → URL вебхука

**Проверка подписи (обязательно):**
- Заголовок: `trbt-signature`
- Алгоритм: **HMAC-SHA256** тела запроса, ключ = API-ключ
- При невалидной подписи → `401`, не обрабатывать

**Повторные попытки Tribute при ошибке доставки (~24ч):**
`5мин → 15мин → 30мин → 1ч → 2ч → 4ч → 8ч → 8ч`

> Обработчик должен быть **идемпотентным** — повторный webhook не создаёт дубликат безлимита.

#### События Shop API (основные)

| Webhook | Когда | Действие backend |
|---------|-------|------------------|
| `shopOrderPaymentReceived` | Успешная оплата | `has_unlimited = true`, уведомить user |
| `shopOrderPaymentFailed` | Ошибка оплаты | Обновить статус заказа, уведомить user |
| `shopOrder` | Заказ создан (status=paid) | Альтернативный триггер grant |
| `shopOrderCancelled` | Отмена | Не выдавать доступ |
| `shopOrderRefunded` | Возврат | `has_unlimited = false`, уведомить user |

**Payload `ShopOrderPayload` (ключевые поля):**
```json
{
  "uuid": "order-uuid",
  "shopId": 123,
  "amount": 4900,
  "currency": "rub",
  "status": "paid",
  "customerId": "123456789",
  "isRecurrent": false
}
```

**Логика обработки:**
```python
def handle_tribute_payment(payload):
    telegram_id = int(payload["customerId"])
    order_uuid = payload["uuid"]

    if already_processed(order_uuid):
        return 200  # idempotent

    user = get_user_by_telegram_id(telegram_id)
    user.has_unlimited = True
    user.funnel_state = "UNLIMITED"
    save_tribute_payment(order_uuid, telegram_id, payload)
    notify_user(telegram_id, "unlimited_activated")
    notify_admin(f"Unlimited purchased: {telegram_id}")
```

#### События Digital Product API (альтернативный режим)

Если используется статический цифровой товар вместо Shop API:

```json
{
  "name": "new_digital_product",
  "created_at": "2025-03-20T01:15:58.332Z",
  "payload": {
    "product_id": 456,
    "amount": 500,
    "currency": "usd",
    "telegram_user_id": 123456789
  }
}
```

Webhook `digitalProductRefund` — отзыв безлимита при возврате.

---

### 9.1.4. Альтернатива: статический цифровой товар

Для быстрого старта без Shop API:

1. В Tribute: Цифровые товары → создать товар «Безлимит AI-анализ»
2. Получить ссылку: `https://t.me/tribute/app?startapp=p456`
3. В Admin UI сохранить в `tribute_product_link`
4. Inline-кнопка в боте ведёт на эту ссылку
5. Webhook `new_digital_product` → grant по `telegram_user_id`

**Минус:** нельзя динамически менять цену из Admin UI без пересоздания товара в Tribute.

---

### 9.1.5. Таблица `tribute_payments`

| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | |
| user_id | UUID FK | |
| telegram_id | BIGINT | |
| order_uuid | VARCHAR UNIQUE | UUID заказа Tribute |
| product_id | INT nullable | Для digital product mode |
| amount | INT | Копейки/центы |
| currency | VARCHAR(3) | rub/usd/eur |
| status | VARCHAR | pending / paid / failed / refunded |
| payment_method | VARCHAR nullable | card / sbp / stars / ton |
| raw_webhook | JSONB | Полный payload |
| created_at | TIMESTAMPTZ | |
| paid_at | TIMESTAMPTZ nullable | |

---

### 9.1.6. Настройки в Admin UI / `app_settings`

| Key | Пример | Описание |
|-----|--------|----------|
| `tribute_enabled` | true | Включить оплату через Tribute |
| `tribute_mode` | `shop_api` / `digital_product` | Режим интеграции |
| `tribute_product_link` | `https://t.me/tribute/app?startapp=p456` | Статическая ссылка (digital_product) |
| `unlimited_price_amount` | 4900 | Цена в копейках |
| `unlimited_price_currency` | rub | Валюта |
| `unlimited_title` | AI Анализ — Безлимит | Название заказа |
| `unlimited_description` | ... | Описание заказа |

---

### 9.1.7. Сравнение с конкурентом

| GrayScheme | Наш продукт |
|------------|-------------|
| Ссылка на диалог с админом (Telegram Business) | Tribute `webappPaymentUrl` |
| Ручная выдача безлимита админом | **Автоматическая** по webhook |
| Цена в config.yaml | Цена в Admin UI → Shop API order |
| Нет платёжной интеграции | Карты, СБП, Stars, TON через Tribute |

---

## 10. Мультиязычность

### Языки MVP (11 как у конкурента)

`ru`, `en`, `hi`, `es`, `az`, `pt`, `br`, `tr`, `ar` + расширяемо

### Хранение

Таблица `translations`:
```
(key, locale, value)
```

Ключи: `bot.start`, `webapp.dashboard.title`, `funnel.register.button`, ...

### Настройки

| Параметр | Описание |
|----------|----------|
| `enabled_languages` | Список кодов для показа в боте |
| `default_language` | Язык по умолчанию |
| `single_language_mode` | Если один язык — пропустить выбор |

> Аналог `lang.yaml` + `EnableLanguages` конкурента, но через Admin UI и PostgreSQL.

### Промокод в переводах

Placeholder `{promo_code}` в строках → подставляется из `app_settings.affiliate_promo_code`.

---

## 11. Подписка на канал

### Настройки
- `channel_id` — ID канала (например `-1001234567890`)
- `channel_url` — ссылка для кнопки «Подписаться»

### Проверка
- Bot API: `getChatMember(chat_id, user_id)`
- Статусы OK: `member`, `administrator`, `creator`
- При fail: остаётся на шаге `CHANNEL_SUBSCRIBED` pending

### Требования
- Bot должен быть **администратором** канала (как у конкурента)

---

## 12. Админ-панель

### Доступ
- `ADMIN_TELEGRAM_IDS` в `.env` (список через запятую)
- Проверка на backend по `initData` / internal bot token

### Функции (parity с /admin4 конкурента)

| # | Функция | API / UI |
|---|---------|----------|
| 1 | Статистика | users, reg, deposits, analyses, blocks |
| 2 | Рассылка | text + optional photo → all active users |
| 3 | Смена реф. ссылки | update `affiliate_ref_url` |
| 4 | Смена промокода | update `affiliate_promo_code` |
| 5 | Выдать безлимит | by telegram_id or forwarded message |
| 6 | Забрать безлимит | revoke |
| 7 | Языки | enable/disable locales |
| 8 | Postback URLs | copy-ready links for partner cabinet |
| 9 | Tribute | цена безлимита, валюта, режим (shop_api / digital_product) |

### Bot admin commands

```
/admin          → inline menu
/admin stats    → краткая статистика
/admin broadcast → запуск сценария рассылки
```

---

## 13. Модель данных (PostgreSQL)

### `users`

| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | |
| telegram_id | BIGINT UNIQUE | |
| username | VARCHAR | |
| language | VARCHAR(5) | ru, en, ... |
| funnel_state | VARCHAR(32) | state machine |
| is_channel_subscribed | BOOL | |
| is_registered | BOOL | |
| is_deposited | BOOL | |
| has_unlimited | BOOL | |
| attempts_count | INT | за текущее окно |
| attempts_window_start | TIMESTAMPTZ | |
| registered_at | TIMESTAMPTZ | |
| deposited_at | TIMESTAMPTZ | |
| deposit_amount | DECIMAL | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |
| is_blocked | BOOL | bot blocked by user |

### `ai_analyses`

| Поле | Тип |
|------|-----|
| id | UUID PK |
| user_id | UUID FK |
| image_path | VARCHAR |
| recommendation | TEXT |
| coefficient | DECIMAL |
| probability_percent | INT |
| explanation | TEXT |
| raw_ai_response | JSONB |
| created_at | TIMESTAMPTZ |

### `postback_events`

| Поле | Тип |
|------|-----|
| id | UUID PK |
| telegram_id | BIGINT |
| event_type | registration / deposit |
| amount | DECIMAL nullable |
| raw_payload | JSONB |
| processed | BOOL |
| created_at | TIMESTAMPTZ |

### `app_settings` (key-value)

| Key | Пример |
|-----|--------|
| affiliate_ref_url | https://... |
| affiliate_promo_code | AIBET776 |
| channel_id | -100... |
| channel_url | https://t.me/... |
| support_url | https://t.me/support |
| unlimited_enabled | true |
| unlimited_price_amount | 4900 |
| unlimited_price_currency | rub |
| tribute_enabled | true |
| tribute_mode | shop_api |
| tribute_product_link | https://t.me/tribute/app?startapp=p456 |
| enabled_languages | ["ru","en"] |
| default_language | ru |
| daily_attempts_limit | 10 |

### `tribute_payments`

См. раздел [9.1.5](#915-таблица-tribute_payments).

### `broadcasts`

| Поле | Тип |
|------|-----|
| id | UUID |
| admin_telegram_id | BIGINT |
| message_text | TEXT |
| sent_count | INT |
| failed_count | INT |
| created_at | TIMESTAMPTZ |

### `translations`

| Поле | Тип |
|------|-----|
| key | VARCHAR |
| locale | VARCHAR(5) |
| value | TEXT |
| UNIQUE(key, locale) | |

---

## 14. REST API

### Auth
```
POST /api/auth/telegram
Body: { "init_data": "..." }  // Telegram WebApp initData
Response: { "token": "jwt...", "user": {...} }
```

### User
```
GET  /api/user/me
GET  /api/user/status          // funnel + attempts + unlimited
POST /api/user/language        { "language": "ru" }
POST /api/user/check-subscription
POST /api/user/analyze         multipart/form-data (screenshot)
GET  /api/user/analyses        // history
GET  /api/user/analyses/{id}
POST /api/payments/unlimited/create   // создать заказ Tribute, вернуть payment URLs
GET  /api/payments/unlimited/status   // статус последнего заказа пользователя
```

### Webhooks (public)
```
GET|POST /api/webhook/postback/registration
GET|POST /api/webhook/postback/deposit
POST     /api/webhook/tribute            // Tribute Shop + Digital Product webhooks
```

### Admin (JWT + admin role)
```
GET  /api/admin/stats
POST /api/admin/broadcast       { "text", "photo_url"? }
PUT  /api/admin/settings        { ... }
PUT  /api/admin/affiliate       { "ref_url", "promo_code" }
POST /api/admin/unlimited/grant { "telegram_id" }
POST /api/admin/unlimited/revoke { "telegram_id" }
GET  /api/admin/users           ?page&search
GET  /api/admin/postback-urls   // generated URLs for partner
```

### Internal (bot-service → backend)
```
POST /api/internal/notify        { "telegram_id", "template", "params" }
GET  /api/internal/user/{telegram_id}
```

---

## 15. Docker Compose

### Сервисы

```yaml
services:
  postgres:      # volume: pg_data
  redis:         # volume: redis_data (optional)
  backend:       # FastAPI, depends on postgres, redis
  bot-service:   # aiogram, depends on backend
  frontend:      # React build → nginx static
  nginx:         # reverse proxy, SSL termination
  backup:        # optional cron pg_dump → backup_data volume
```

### Volumes

| Volume | Назначение |
|--------|------------|
| `pg_data` | PostgreSQL data |
| `storage_data` | Uploaded screenshots, exports |
| `backup_data` | DB dumps (daily retention configurable) |
| `redis_data` | Redis persistence (optional) |

### `.env` (минимальный набор)

```env
# Telegram
BOT_TOKEN=
WEBAPP_URL=https://your-domain.com
ADMIN_TELEGRAM_IDS=123456789

# Database
POSTGRES_USER=bot
POSTGRES_PASSWORD=
POSTGRES_DB=ai_bet_bot

# AI
AI_PROVIDER=openai
OPENAI_API_KEY=

# App
DEFAULT_LANGUAGE=ru
DAILY_ATTEMPTS_LIMIT=10

# Affiliate (можно задать позже через Admin UI)
AFFILIATE_REF_URL=
AFFILIATE_PROMO_CODE=
CHANNEL_ID=
CHANNEL_URL=
SUPPORT_URL=

# Tribute (платёжная система)
TRIBUTE_API_KEY=
TRIBUTE_SHOP_ID=
```

### Установка для покупателя (vs конкурент)

```bash
git clone ...
cp .env.example .env
# заполнить BOT_TOKEN, ADMIN_TELEGRAM_IDS, домен
docker compose up -d
# открыть бота → /admin → вставить реф. ссылку и postback URLs в партнёрку
```

**5 шагов** вместо 11+ у GrayScheme.

---

## 16. Безопасность

- Валидация `initData` Telegram (HMAC-SHA256)
- Postback webhook: optional secret `?key=...` или IP whitelist
- Admin routes только для `ADMIN_TELEGRAM_IDS`
- Secrets только в `.env`, не в репозитории
- Rate limit на `/analyze` (10/day + global anti-abuse)
- Sanitize uploaded images, scan size/type
- JWT short-lived для Web App sessions
- **Tribute webhook:** обязательная проверка `trbt-signature` (HMAC-SHA256)
- Идемпотентность обработки платежей по `order_uuid`

---

## 17. Нефункциональные требования

| Требование | Target |
|------------|--------|
| Uptime | 99.5%+ |
| AI response | ≤ 15 sec p95 |
| API response | ≤ 200ms (non-AI) |
| Concurrent users | 1000+ (horizontal scale backend) |
| Data persistence | volumes + daily backup |
| Logs | structured JSON, rotation |
| Zero license checks | no phone-home, no expiry |

---

## 18. MVP — этапы разработки

### Phase 1 — Core (2–3 недели)
- [ ] Docker Compose scaffold
- [ ] PostgreSQL + Alembic migrations
- [ ] FastAPI: auth, user, postback webhooks
- [ ] Bot: /start, язык, подписка, inline menu
- [ ] Funnel state machine
- [ ] Admin: ref link, stats (basic)

### Phase 2 — AI + Web App (2–3 недели)
- [ ] React Web App + Telegram SDK
- [ ] Upload screenshot + AI analysis
- [ ] Attempts limit (10/24h)
- [ ] History, dashboard
- [ ] Postback registration + deposit flow E2E
- [ ] Tribute: создание заказа + webhook + auto-grant безлимита

### Phase 3 — Admin + Polish (1–2 недели)
- [ ] Admin Web App panel
- [ ] Broadcast
- [ ] Unlimited grant/revoke (ручной fallback)
- [ ] Tribute settings в Admin UI (цена, валюта, режим)
- [ ] Translations (11 langs seed)
- [ ] Backup cron container
- [ ] Nginx + SSL

### Phase 4 — Optional
- [ ] Redis rate limiting
- [ ] Worker for async broadcasts
- [ ] Telegram channel report mirror
- [ ] Analytics dashboard
- [ ] A/B funnel variants

---

## 19. Критерии приёмки

1. Пользователь проходит воронку: язык → канал → рег → депозит → AI-анализ
2. Postback регистрации и депозита обновляют статус без ручного вмешательства
3. 10 попыток/24ч работают; безлимит снимает лимит
4. Оплата безлимита через Tribute: заказ → оплата → webhook → автоматический grant
5. Web App открывается из inline-кнопки, показывает актуальные попытки
6. Admin меняет реф. ссылку и промокод без перезапуска (hot reload settings)
7. Admin выдаёт/забирает безлимит вручную (fallback)
8. Рассылка доходит всем незаблокировавшим бота
9. `docker compose up` поднимает всё с нуля; данные переживают restart
10. Бэкап БД лежит в `backup_data` volume
11. Webhook Tribute проверяет подпись `trbt-signature`, обработка идемпотентна
12. **Нет** проверок лицензии, срока 30 дней, привязки к машине

---

## 20. Справка: маппинг «конкурент → наш продукт»

| GrayScheme | Наш продукт |
|------------|-------------|
| `config.yaml` | `.env` + `app_settings` + Admin UI |
| `lang.yaml` | `translations` table + Admin UI |
| `user.db` (SQLite) | PostgreSQL |
| `start.cmd` (Windows) | `docker compose up -d` |
| Бот А + Бот Б | Один bot-service |
| Канал Б + sendMessage postback | HTTP webhook `/api/webhook/postback/*` |
| `/admin4` | `/admin` + Web App Admin |
| Web App activation @bivenmo | Автоматически через @BotFather Menu Button |
| License / 30 days | **Нет** — бессрочная лицензия покупателя |
| Оплата безлимита (Telegram Business link) | **Tribute** Shop API + webhook |
| Ручная выдача безлимита | Авто-grant + ручной fallback |
| FileMan.exe / Defender issues | Нет бинарников, только Docker |

---

## 21. Ссылки на research-материалы и документацию

### Research (конкурент)
- YouTube обзор (31 мин): `research/01_video_youtube_transcription.txt`
- Видео про языки (3 мин): `research/02_video_langsignalbot421_transcription.txt`
- Парсинг сайта конкурента: `research/03_website_parsed_content.md`
- Оригинал: https://grayscheme.com/364-signalnyj-bot-dlja-betting-arbitrazha-trafika-ai-analiz-stavok.html

### Tribute (платёжная система)
- [API Магазина](https://wiki.tribute.tg/ru/for-shops/api-magazina)
- [Методы Shop API](https://wiki.tribute.tg/ru/for-shops/api-magazina/metody)
- [Вебхуки Shop API](https://wiki.tribute.tg/ru/for-shops/api-magazina/vebkhuki)
- [Models](https://wiki.tribute.tg/ru/for-shops/api-magazina/models)
- [Интеграция цифровых товаров в свой продукт](https://wiki.tribute.tg/ru/for-content-creators/digital-product/integrating-digital-products-into-your-product)
- [Полный индекс документации](https://wiki.tribute.tg/llms.txt)
