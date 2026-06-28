#!/usr/bin/env bash
# AI Bet Bot — полный установщик для Ubuntu 24.04
# Запуск (с сервера заказчика):
#   curl -fsSL https://cwais.ru/b9kR2xW4pQ/install.sh | sudo bash

set -euo pipefail

CUSTOMER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${CUSTOMER_DIR}/../.." && pwd)"
if [[ -f "${REPO_ROOT}/docker-compose.yml" ]]; then
  INSTALL_DIR="${INSTALL_DIR:-$REPO_ROOT}"
fi
# shellcheck source=lib/common.sh
source "${CUSTOMER_DIR}/lib/common.sh"
# shellcheck source=lib/validate.sh
source "${CUSTOMER_DIR}/lib/validate.sh"
# shellcheck source=lib/dns.sh
source "${CUSTOMER_DIR}/lib/dns.sh"
# shellcheck source=lib/env.sh
source "${CUSTOMER_DIR}/lib/env.sh"

GIT_REPO="${GIT_REPO:-https://github.com/lyfmi/ai-stvaki-anal.git}"

usage() {
  cat <<EOF
AI Bet Bot Installer v${INSTALLER_VERSION}

Usage:
  sudo bash install.sh              Интерактивная установка
  sudo bash install.sh --dry-run    Проверка без изменений системы
  sudo bash install.sh --help

Быстрый старт (с чистого сервера):
  curl -fsSL https://cwais.ru/b9kR2xW4pQ/install.sh | sudo bash
EOF
}

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --help|-h) usage; exit 0 ;;
    *) warn "Неизвестный аргумент: $arg" ;;
  esac
done

mkdir -p "$(dirname "$LOG_FILE")"
touch "$LOG_FILE"

banner() {
  echo ""
  echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════╗${NC}"
  echo -e "${BOLD}${CYAN}║     AI Bet Bot — установка на сервер         ║${NC}"
  echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════╝${NC}"
  echo ""
  echo "Скрипт задаст 8 простых вопросов. У каждого вопроса есть подсказка в скобках."
  echo "Большинство данных берётся из Telegram — технических знаний не нужно."
  echo ""
}

collect_inputs() {
  local server_ip
  server_ip="$(get_public_ip)"
  [[ -n "$server_ip" ]] || fail "Не удалось определить публичный IP сервера."

  echo -e "${BOLD}Шаг 1 из 8. Домен и DNS${NC}"
  echo "Это адрес сайта бота. Домен покупается на Reg.ru, Timeweb, Cloudflare и т.п."
  echo "Публичный IP этого сервера (нужен для DNS): ${GREEN}${server_ip}${NC}"
  echo ""
  prompt_required BASE_DOMAIN "Введите ваш домен (только название, без https:// — например moybet.ru, тот что купили у регистратора)"
  BASE_DOMAIN="$(normalize_domain "$BASE_DOMAIN")"
  validate_domain "$BASE_DOMAIN" || fail "Некорректный домен: ${BASE_DOMAIN}"

  local suggested
  suggested="$(suggest_subdomain "$BASE_DOMAIN" "tgbot")"
  prompt_optional APP_DOMAIN "Адрес для бота (обычно tgbot.вашдомен.ru — просто нажмите Enter, если не знаете что менять)" "$suggested"
  APP_DOMAIN="$(normalize_domain "$APP_DOMAIN")"
  validate_domain "$APP_DOMAIN" || fail "Некорректный поддомен: ${APP_DOMAIN}"

  echo ""
  echo -e "${YELLOW}Сейчас нужно привязать домен к серверу.${NC}"
  echo "Зайдите в личный кабинет там, где покупали домен → раздел «DNS» / «Управление зоной»."
  echo "Создайте новую запись:"
  echo -e "  ${BOLD}Тип:${NC} A"
  echo -e "  ${BOLD}Имя / Host / Поддомен:${NC} tgbot  (без .${BASE_DOMAIN})"
  echo -e "  ${BOLD}Значение / IP:${NC} ${server_ip}"
  echo -e "  ${BOLD}Итоговый адрес:${NC} ${APP_DOMAIN}"
  echo ""
  echo "Сохраните запись. Обновление занимает обычно 5–15 минут."
  confirm "DNS-запись создана и сохранена? (y — да, продолжаем)" || fail "Создайте DNS-запись в личном кабинете домена и запустите установщик снова."

  if [[ "$DRY_RUN" != "1" ]]; then
    echo ""
    echo "Ждём, пока домен «привяжется» к серверу..."
    wait_for_dns "$APP_DOMAIN" "$server_ip" 30 30
  fi

  echo ""
  echo -e "${BOLD}Шаг 2 из 8. Telegram-бот${NC}"
  echo "1) Откройте в Telegram: @BotFather"
  echo "2) Напишите: /newbot"
  echo "3) Придумайте имя бота (например: AI Bet Analysis)"
  echo "4) Придумайте username — должен заканчиваться на bot (например: MyBetAIBot_bot)"
  echo "5) BotFather пришлёт длинный ключ — это и есть Token"
  echo ""
  prompt_required BOT_TOKEN "Bot Token (скопируйте из @BotFather после /newbot, выглядит как 123456789:AAHxxx...)"
  validate_bot_token "$BOT_TOKEN" || fail "Некорректный формат Bot Token. Скопируйте ключ целиком из @BotFather."

  prompt_optional BOT_USERNAME "Username бота (тот что вы придумали в @BotFather, без символа @ — например MyBetAIBot_bot)" ""
  prompt_optional BOT_DISPLAY_NAME "Имя бота для отображения (как назвали в @BotFather, или Enter — оставить по умолчанию)" "AI Bet Analysis"

  echo ""
  echo -e "${BOLD}Шаг 3 из 8. Ваш Telegram ID (вы — главный админ)${NC}"
  echo "1) Откройте в Telegram: @userinfobot или @getmyid_bot"
  echo "2) Нажмите Start / Отправьте любое сообщение"
  echo "3) Бот пришлёт ваш Id — это число, например 7649494487"
  echo ""
  echo -e "${GREEN}После установки ваш аккаунт активируется автоматически —${NC}"
  echo -e "${GREEN}воронку (подписка, регистрация 1win) проходить не нужно.${NC}"
  echo ""
  prompt_required ADMIN_TELEGRAM_ID "Ваш Telegram ID (число из @userinfobot — только цифры, без @username)"
  validate_telegram_id "$ADMIN_TELEGRAM_ID" || fail "Некорректный Telegram ID. Нужно число из @userinfobot."

  echo ""
  echo -e "${BOLD}Шаг 4 из 8. Канал подписки (куда ведёт воронка)${NC}"
  echo "1) Создайте канал в Telegram: Меню → Новый канал → название + описание"
  echo "2) Сделайте ссылку: Настройки канала → Пригласительные ссылки → Создать"
  echo "3) Узнайте ID канала: перешлите любой пост канала боту @getmyid_bot"
  echo "   ID будет вида -1001234567890 (обязательно с минусом!)"
  echo "4) Добавьте вашего бота @${BOT_USERNAME:-yourbot} в админы канала:"
  echo "   Настройки канала → Администраторы → Добавить → найдите бота"
  echo ""
  prompt_required SUB_CHANNEL_ID "ID канала подписки (из @getmyid_bot после пересылки поста, формат -100...)"
  validate_telegram_id "$SUB_CHANNEL_ID" || fail "Некорректный ID канала. Перешлите пост канала в @getmyid_bot."
  prompt_required SUB_CHANNEL_URL "Ссылка на канал (из «Пригласительные ссылки», формат https://t.me/название_канала)"
  validate_channel_url "$SUB_CHANNEL_URL" || fail "Ссылка должна быть вида https://t.me/название_канала"

  echo ""
  echo -e "${BOLD}Шаг 5 из 8. Канал оповещений (только для вас)${NC}"
  echo "1) Создайте второй канал или закрытую группу — сюда будут приходить уведомления:"
  echo "   «пользователь зарегистрировался», «сделал депозит», «оплатил безлимит»"
  echo "2) Добавьте туда вашего бота администратором (как в шаге 4)"
  echo "3) Узнайте ID: перешлите пост канала в @getmyid_bot"
  echo ""
  prompt_required REPORTS_CHANNEL_ID "ID канала оповещений (из @getmyid_bot, формат -100..., бот должен быть админом)"
  validate_telegram_id "$REPORTS_CHANNEL_ID" || fail "Некорректный ID. Перешлите пост канала в @getmyid_bot."
  prompt_optional REPORTS_CHANNEL_URL "Ссылка на канал оповещений (необязательно, Enter — пропустить)" ""

  echo ""
  echo -e "${BOLD}Шаг 6 из 8. Партнёрка 1win${NC}"
  echo "Данные выдаёт ваш менеджер 1win после подключения партнёрки."
  echo ""
  prompt_required AFFILIATE_REF_URL "Реферальная ссылка 1win (ссылка от менеджера, начинается с https://)"
  validate_https_url "$AFFILIATE_REF_URL" || fail "Ссылка должна начинаться с https:// — скопируйте из личного кабинета 1win."
  prompt_required AFFILIATE_PROMO_CODE "Промокод 1win (слово/код для пользователей, например GOMATCH — от менеджера 1win)"

  echo ""
  echo -e "${BOLD}Шаг 7 из 8. Tribute — оплата безлимита (можно пропустить)${NC}"
  echo "Если оплату через Tribute пока не настраиваете — нажимайте Enter на всех полях."
  echo "Если настраиваете:"
  echo "  1) Зарегистрируйтесь на tribute.tg"
  echo "  2) Создайте магазин / товар"
  echo "  3) В настройках магазина найдите API Key, Shop ID и Webhook Secret"
  echo "  (Webhook URL скрипт покажет в конце установки)"
  echo ""
  prompt_optional TRIBUTE_API_KEY "Tribute API Key (из настроек магазина на tribute.tg, Enter — пропустить)" ""
  prompt_optional TRIBUTE_SHOP_ID "Tribute Shop ID (числовой ID магазина на tribute.tg, Enter — пропустить)" ""
  prompt_optional TRIBUTE_WEBHOOK_SECRET "Tribute Webhook Secret (секрет для webhook в tribute.tg, Enter — пропустить)" ""
  prompt_optional UNLIMITED_PRICE_AMOUNT "Цена безлимита в копейках (4900 = 49 руб., Enter — оставить 49 руб.)" "4900"

  if [[ -n "${TRIBUTE_API_KEY:-}" ]]; then
    TRIBUTE_ENABLED="true"
    UNLIMITED_ENABLED="true"
  else
    TRIBUTE_ENABLED="false"
    UNLIMITED_ENABLED="false"
  fi

  echo ""
  echo -e "${BOLD}Шаг 8 из 8. Финальные настройки${NC}"
  prompt_optional LETSENCRYPT_EMAIL "Email для SSL-сертификата (любой ваш email — для уведомлений о продлении, Enter — admin@${BASE_DOMAIN})" "admin@${BASE_DOMAIN}"
  prompt_optional SUPPORT_URL "Ссылка на вашу поддержку в Telegram (Enter — автоматически на бота @${BOT_USERNAME:-support})" "https://t.me/${BOT_USERNAME:-support}"

  export APP_DOMAIN BASE_DOMAIN BOT_TOKEN BOT_USERNAME BOT_DISPLAY_NAME
  export ADMIN_TELEGRAM_ID SUB_CHANNEL_ID SUB_CHANNEL_URL
  export REPORTS_CHANNEL_ID REPORTS_CHANNEL_URL
  export AFFILIATE_REF_URL AFFILIATE_PROMO_CODE
  export TRIBUTE_API_KEY TRIBUTE_SHOP_ID TRIBUTE_WEBHOOK_SECRET
  export TRIBUTE_ENABLED UNLIMITED_ENABLED UNLIMITED_PRICE_AMOUNT
  export LETSENCRYPT_EMAIL SUPPORT_URL
  export CHANNEL_ID="$SUB_CHANNEL_ID"
  export CHANNEL_URL="$SUB_CHANNEL_URL"
}

install_system_packages() {
  info "Установка системных пакетов..."
  run_cmd apt-get update -qq
  run_cmd apt-get install -y -qq \
    ca-certificates curl gnupg lsb-release \
    nginx certbot python3-certbot-nginx \
    dnsutils openssl git ufw

  if ! command -v docker >/dev/null 2>&1; then
    info "Установка Docker..."
    if [[ "$DRY_RUN" != "1" ]]; then
      install -m 0755 -d /etc/apt/keyrings
      curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
      chmod a+r /etc/apt/keyrings/docker.asc
      echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
        $(. /etc/os-release && echo "${VERSION_CODENAME}") stable" \
        >/etc/apt/sources.list.d/docker.list
      apt-get update -qq
      apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
      systemctl enable --now docker
    fi
  fi
  ok "Docker и nginx готовы"
}

clone_or_update_repo() {
  if [[ -d "${INSTALL_DIR}/.git" ]]; then
    info "Репозиторий уже есть — git pull"
    run_cmd git -C "$INSTALL_DIR" pull --ff-only origin main || true
  else
    info "Клонирование ${GIT_REPO} → ${INSTALL_DIR}"
    run_cmd mkdir -p "$(dirname "$INSTALL_DIR")"
    run_cmd git clone --depth 1 "$GIT_REPO" "$INSTALL_DIR"
  fi
}

start_docker_stack() {
  info "Сборка и запуск Docker Compose..."
  run_cmd bash -c "cd '${INSTALL_DIR}' && docker compose up -d --build"

  if [[ "$DRY_RUN" == "1" ]]; then
    return 0
  fi

  info "Ожидание backend /health..."
  local attempt=0
  while (( attempt < 60 )); do
    if curl -fsS "http://127.0.0.1:8010/health" >/dev/null 2>&1; then
      ok "Backend отвечает"
      return 0
    fi
    sleep 5
    ((attempt++))
  done
  fail "Backend не запустился. Проверьте: cd ${INSTALL_DIR} && docker compose logs backend"
}

configure_app_settings() {
  info "Запись настроек каналов, 1win и Tribute в БД..."
  info "Активация вашего аккаунта (без воронки)..."
  if [[ "$DRY_RUN" == "1" ]]; then
    info "[dry-run] configure_app skipped"
    return 0
  fi

  export CHANNEL_ID="$SUB_CHANNEL_ID"
  export CHANNEL_URL="$SUB_CHANNEL_URL"
  export REPORTS_CHANNEL_ID
  export AFFILIATE_REF_URL AFFILIATE_PROMO_CODE
  export TRIBUTE_API_KEY="${TRIBUTE_API_KEY:-}"
  export TRIBUTE_SHOP_ID="${TRIBUTE_SHOP_ID:-}"
  export TRIBUTE_WEBHOOK_SECRET="${TRIBUTE_WEBHOOK_SECRET:-}"
  export TRIBUTE_ENABLED UNLIMITED_ENABLED
  export UNLIMITED_PRICE_AMOUNT="${UNLIMITED_PRICE_AMOUNT:-4900}"
  export UNLIMITED_PRICE_CURRENCY="rub"
  export SUPPORT_URL
  export ADMIN_TELEGRAM_ID

  docker compose -f "${INSTALL_DIR}/docker-compose.yml" exec -T \
    -e CHANNEL_ID -e CHANNEL_URL -e REPORTS_CHANNEL_ID \
    -e AFFILIATE_REF_URL -e AFFILIATE_PROMO_CODE \
    -e TRIBUTE_API_KEY -e TRIBUTE_SHOP_ID -e TRIBUTE_WEBHOOK_SECRET \
    -e TRIBUTE_ENABLED -e UNLIMITED_ENABLED \
    -e UNLIMITED_PRICE_AMOUNT -e UNLIMITED_PRICE_CURRENCY \
    -e SUPPORT_URL -e ADMIN_TELEGRAM_ID \
    backend python - < "${INSTALL_DIR}/deploy/customer/scripts/configure_app.py"
  ok "Настройки приложения сохранены, ваш аккаунт активирован"
}

setup_nginx_ssl() {
  local nginx_available="/etc/nginx/sites-available/${APP_DOMAIN}"
  local nginx_enabled="/etc/nginx/sites-enabled/${APP_DOMAIN}"
  local template="${INSTALL_DIR}/deploy/customer/templates/nginx.site.conf.template"

  info "Настройка nginx..."
  render_nginx_config "$template" "$nginx_available" "$APP_DOMAIN"
  run_cmd ln -sf "$nginx_available" "$nginx_enabled"
  run_cmd rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
  run_cmd nginx -t
  run_cmd systemctl reload nginx

  info "Получение SSL-сертификата Let's Encrypt..."
  if [[ "$DRY_RUN" == "1" ]]; then
    info "[dry-run] certbot skipped"
    return 0
  fi

  certbot --nginx -d "$APP_DOMAIN" --non-interactive --agree-tos -m "$LETSENCRYPT_EMAIL" --redirect
  run_cmd nginx -t
  run_cmd systemctl reload nginx
  ok "HTTPS активен: https://${APP_DOMAIN}"
}

setup_firewall() {
  info "Настройка UFW (22, 80, 443)..."
  if [[ "$DRY_RUN" == "1" ]]; then
    return 0
  fi
  ufw allow OpenSSH >/dev/null 2>&1 || ufw allow 22/tcp
  ufw allow 80/tcp
  ufw allow 443/tcp
  ufw --force enable
}

setup_bot_webapp() {
  if [[ "$DRY_RUN" == "1" ]] || [[ -z "${BOT_TOKEN:-}" ]]; then
    return 0
  fi
  info "Настройка Mini App URL в BotFather..."
  local webapp_url="https://${APP_DOMAIN}"
  curl -fsS "https://api.telegram.org/bot${BOT_TOKEN}/setChatMenuButton" \
    -d "menu_button={\"type\":\"web_app\",\"text\":\"Open App\",\"web_app\":{\"url\":\"${webapp_url}\"}}" \
    >/dev/null 2>&1 || warn "setChatMenuButton не применился — настройте Menu Button в @BotFather вручную"

  run_cmd bash -c "cd '${INSTALL_DIR}' && docker compose restart bot-service"
  ok "Webhook бота будет установлен автоматически при старте bot-service"
}

print_summary() {
  local base="https://${APP_DOMAIN}"
  cat <<EOF

${GREEN}${BOLD}╔══════════════════════════════════════════════════════════╗
║              УСТАНОВКА ЗАВЕРШЕНА                         ║
╚══════════════════════════════════════════════════════════╝${NC}

${BOLD}Mini App / Web:${NC}     ${base}
${BOLD}Webhook бота:${NC}       ${base}/telegram/webhook
${BOLD}Health check:${NC}       ${base}/health

${BOLD}Postback регистрация:${NC}
  ${base}/api/webhook/postback/registration?sub1={telegram_id}

${BOLD}Postback депозит:${NC}
  ${base}/api/webhook/postback/deposit?sub1={telegram_id}&amount={sum}

${BOLD}Tribute webhook:${NC}
  ${base}/api/webhook/tribute

${BOLD}Проект на сервере:${NC}  ${INSTALL_DIR}
${BOLD}Лог установки:${NC}      ${LOG_FILE}

${YELLOW}Проверьте в Telegram:${NC}
  1. /start у бота @${BOT_USERNAME:-yourbot}
  2. Mini App открывается по кнопке меню
  3. Админка: Mini App → Profile → Admin (ваш ID: ${ADMIN_TELEGRAM_ID})

${YELLOW}BotFather (если меню не появилось):${NC}
  /setmenubutton → выберите бота → Web App → URL: ${base}

${YELLOW}Полезные команды:${NC}
  cd ${INSTALL_DIR} && docker compose ps
  cd ${INSTALL_DIR} && docker compose logs -f backend
  cd ${INSTALL_DIR} && docker compose restart

EOF
}

main() {
  banner
  require_root
  require_ubuntu_2404

  if [[ "$DRY_RUN" == "1" ]]; then
    warn "Режим --dry-run: система не будет изменена."
  fi

  collect_inputs
  install_system_packages
  clone_or_update_repo
  write_env_file "${INSTALL_DIR}/.env"
  start_docker_stack
  configure_app_settings
  setup_nginx_ssl
  setup_firewall
  setup_bot_webapp
  print_summary
}

main "$@"
