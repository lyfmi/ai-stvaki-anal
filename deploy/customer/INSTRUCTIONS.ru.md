# Инструкция для заказчика: установка AI Bet Bot

Полный путь от покупки домена и сервера до работающего бота с Mini App.

---

## Что получится в итоге

- Telegram-бот с воронкой (подписка → регистрация 1win → депозит)
- Mini App для анализа скриншотов
- Админ-панель в Mini App (Profile → Admin)
- Postback URL для партнёрки 1win
- Опционально: оплата безлимита через Tribute

---

## Часть 1. Подготовка (до сервера)

### 1.1 Домен

1. Купите домен у регистратора (Reg.ru, Timeweb, Cloudflare и т.д.).
2. Запомните домен, например: `mybet.ru`.

### 1.2 Сервер

Рекомендуции:

| Параметр | Минимум |
|----------|---------|
| ОС | **Ubuntu 24.04 LTS** |
| CPU | 2 vCPU |
| RAM | 4 GB |
| Диск | 40 GB SSD |
| Порты | 22 (SSH), 80, 443 |

Подойдут: Timeweb Cloud, Selectel, Hetzner, DigitalOcean.

После создания сервера вы получите **IP-адрес** (например `185.12.34.56`) и **root-пароль** или SSH-ключ.

### 1.3 Подключение по SSH

```bash
ssh root@185.12.34.56
```

(подставьте IP вашего сервера)

---

## Часть 2. Автоматическая установка

### 2.1 Одна команда

На **чистом Ubuntu 24.04** выполните:

```bash
curl -fsSL https://cwais.ru/b9kR2xW4pQ/install.sh | sudo bash
```

Скрипт сам:

- обновит систему и установит Docker, Git, nginx, certbot
- спросит все нужные данные по шагам
- подождёт DNS (до ~15 минут)
- развернёт проект в `/opt/ai-bot-stavki`
- получит SSL-сертификат
- настроит webhook бота

Лог установки: `/var/log/ai-bot-stavki-install.log`

---

## Часть 3. Что подготовить до запуска скрипта

### Шаг A — DNS (скрипт подскажет)

Создайте **A-запись**:

| Поле | Значение |
|------|----------|
| Тип | A |
| Host / Имя | `tgbot` |
| Значение | IP вашего сервера |
| TTL | 300–3600 |

Итоговый адрес: `tgbot.mybet.ru` (скрипт предложит поддомен автоматически).

### Шаг B — Telegram-бот (@BotFather)

1. Откройте [@BotFather](https://t.me/BotFather)
2. `/newbot`
3. Имя бота (например `AI Bet Analysis`)
4. Username (например `MyBetAIBot_bot`) — должен заканчиваться на `bot`
5. Сохраните **HTTP API Token** (`123456789:AA...`)

### Шаг C — Ваш Telegram ID (админ)

1. Откройте [@userinfobot](https://t.me/userinfobot) или [@getmyid_bot](https://t.me/getmyid_bot)
2. Скопируйте **Id** (число, например `7649494487`)

### Шаг D — Канал подписки (воронка)

1. Создайте Telegram-канал с прогнозами/сигналами
2. Сделайте ссылку-приглашение: `https://t.me/your_channel`
3. Узнайте **ID канала**:
   - перешлите любой пост канала боту [@getmyid_bot](https://t.me/getmyid_bot)
   - или добавьте [@RawDataBot](https://t.me/RawDataBot) — ID будет вида `-1001234567890`
4. **Добавьте вашего бота администратором** канала (достаточно права «видеть участников»)

### Шаг E — Канал оповещений

1. Создайте второй канал или закрытую группу **только для вас**
2. Туда будут приходить уведомления: регистрации, депозиты, оплаты
3. Добавьте бота **администратором**
4. Сохраните ID канала (формат `-100...`)

### Шаг F — Партнёрка 1win

Подготовьте от менеджера 1win:

- **Реферальную ссылку** (https://...)
- **Промокод** (например `GOMATCH`)

### Шаг G — Tribute (опционально)

Если нужна продажа безлимита:

1. Зарегистрируйтесь на [tribute.tg](https://tribute.tg)
2. Создайте товар/магазин
3. Подготовьте: **API Key**, **Shop ID**, **Webhook Secret**
4. Webhook URL (скрипт покажет после установки):
   `https://tgbot.ВАШ-ДОМЕН.ru/api/webhook/tribute`

Если Tribute пока не нужен — нажимайте Enter на этих полях.

---

## Часть 4. Диалог установщика (по шагам)

| Шаг | Что спрашивает |
|-----|----------------|
| 1 | Домен, поддомен, проверка DNS |
| 2 | Bot Token, username, имя |
| 3 | Ваш Telegram ID (админ) |
| 4 | ID и ссылка канала подписки |
| 5 | ID канала оповещений |
| 6 | Реф. ссылка и промокод 1win |
| 7 | Данные Tribute (или пропуск) |
| 8 | Email для SSL |

---

## Часть 5. После установки

### Проверка

1. Откройте бота → `/start` — должна начаться воронка
2. Кнопка меню **Open App** — открывает Mini App
3. Пройдите воронку тестовым аккаунтом
4. Mini App → **Profile → Admin** — админка (только ваш ID)

### Postback URL для 1win

Скрипт выведет в конце, также в админке → **postback**:

```
https://tgbot.ВАШ-ДОМЕН.ru/api/webhook/postback/registration?sub1={telegram_id}
https://tgbot.ВАШ-ДОМЕН.ru/api/webhook/postback/deposit?sub1={telegram_id}&amount={sum}
```

Передайте их менеджеру 1win.

### BotFather — Mini App (если кнопка меню не появилась)

```
/setmenubutton
→ выберите бота
→ Web App
→ URL: https://tgbot.ВАШ-ДОМЕН.ru
```

---

## Часть 6. Управление на сервере

```bash
cd /opt/ai-bot-stavki

# Статус контейнеров
docker compose ps

# Логи
docker compose logs -f backend
docker compose logs -f bot-service

# Перезапуск
docker compose restart

# Обновление после изменений в Git
git pull
docker compose up -d --build
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.seeds.run
```

---

## Часть 7. AI-анализ

AI работает через **Nous Inference API** (модель `stepfun/step-3.7-flash:free`).  
Ключ уже прописан в установщике — дополнительная настройка не требуется.

---

## Часть 8. Troubleshooting

| Проблема | Решение |
|----------|---------|
| DNS не резолвится | Подождите 15–30 мин, проверьте A-запись |
| certbot ошибка | Убедитесь что порт 80 открыт и DNS указывает на сервер |
| Бот не отвечает | `docker compose logs bot-service`, проверьте BOT_TOKEN |
| Не проверяет подписку | Бот должен быть админом канала |
| Mini App 403 | Пройдите воронку до депозита |
| SSL expired | `certbot renew` |

---

## Контакты разработчика

При проблемах с установкой отправьте файл:

```bash
cat /var/log/ai-bot-stavki-install.log
```

и вывод:

```bash
cd /opt/ai-bot-stavki && docker compose ps && docker compose logs --tail=50 backend
```

---

## Ссылка на установщик

```bash
curl -fsSL https://cwais.ru/b9kR2xW4pQ/install.sh | sudo bash
```

Документация в репозитории: `deploy/customer/INSTRUCTIONS.ru.md`
