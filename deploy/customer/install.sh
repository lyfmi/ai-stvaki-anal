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
}

collect_inputs() {
  local server_ip
  server_ip="$(get_public_ip)"
  [[ -n "$server_ip" ]] || fail "Не удалось определить публичный IP сервера."

  echo -e "${BOLD}Шаг 1. Домен и DNS${NC}"
  echo "Публичный IP этого сервера: ${GREEN}${server_ip}${NC}"
  echo ""
  prompt_required BASE_DOMAIN "Введите ваш домен (например example.ru, без https://)"
  BASE_DOMAIN="$(normalize_domain "$BASE_DOMAIN")"
  validate_domain "$BASE_DOMAIN" || fail "Некорректный домен: ${BASE_DOMAIN}"

  local suggested
  suggested="$(suggest_subdomain "$BASE_DOMAIN" "tgbot")"
  prompt_optional APP_DOMAIN "Поддомен для бота и Mini App" "$suggested"
  APP_DOMAIN="$(normalize_domain "$APP_DOMAIN")"
  validate_domain "$APP_DOMAIN" || fail "Некорректный поддомен: ${APP_DOMAIN}"

  echo ""
  echo -e "${YELLOW}Создайте DNS A-запись у регистратора:${NC}"
  echo -e "  Тип: ${BOLD}A${NC}"
  echo -e "  Имя/Host: ${BOLD}tgbot${NC} (или часть до .${BASE_DOMAIN})"
  echo -e "  Значение: ${BOLD}${server_ip}${NC}"
  echo -e "  Полный домен: ${BOLD}${APP_DOMAIN}${NC}"
  echo ""
  echo "Распространение DNS обычно занимает 5–15 минут."
  confirm "DNS A-запись уже создана?" || fail "Создайте DNS-запись и запустите установщик снова."

  if [[ "$DRY_RUN" != "1" ]]; then
    wait_for_dns "$APP_DOMAIN" "$server_ip" 30 30
  fi

  echo ""
  echo -e "${BOLD}Шаг 2. Telegram-бот${NC}"
  echo "Создайте бота через @BotFather: /newbot → имя → username."
  echo "Скопируйте HTTP API Token."
  prompt_required BOT_TOKEN "Bot Token (123456789:AA...)"
  validate_bot_token "$BOT_TOKEN" || fail "Некорректный формат Bot Token."

  prompt_optional BOT_USERNAME "Username бота (без @, например MyBetAIBot)" ""
  prompt_optional BOT_DISPLAY_NAME "Отображаемое имя бота" "AI Bet Analysis"

  echo ""
  echo -e "${BOLD}Шаг 3. Ваш Telegram ID (админ)${NC}"
  echo "Узнайте ID через @userinfobot или @getmyid_bot."
  prompt_required ADMIN_TELEGRAM_ID "Ваш Telegram numeric ID"
  validate_telegram_id "$ADMIN_TELEGRAM_ID" || fail "Некорректный Telegram ID."

  echo ""
  echo -e "${BOLD}Шаг 4. Канал подписки (воронка)${NC}"
  echo "Создайте публичный или приватный канал с прогнозами."
  echo "Добавьте бота @${BOT_USERNAME:-yourbot} администратором (можно без постинга)."
  prompt_required SUB_CHANNEL_ID "ID канала (например -1001234567890)"
  validate_telegram_id "$SUB_CHANNEL_ID" || fail "Некорректный ID канала."
  prompt_required SUB_CHANNEL_URL "Ссылка на канал (https://t.me/...)"
  validate_channel_url "$SUB_CHANNEL_URL" || fail "Ссылка должна быть вида https://t.me/channel"

  echo ""
  echo -e "${BOLD}Шаг 5. Канал оповещений (postback / оплаты)${NC}"
  echo "Создайте второй канал/группу только для уведомлений о регистрациях и депозитах."
  echo "Добавьте туда бота администратором."
  prompt_required REPORTS_CHANNEL_ID "ID канала оповещений"
  validate_telegram_id "$REPORTS_CHANNEL_ID" || fail "Некорректный ID канала оповещений."
  prompt_optional REPORTS_CHANNEL_URL "Ссылка на канал оповещений" ""

  echo ""
  echo -e "${BOLD}Шаг 6. Партнёрка 1win${NC}"
  prompt_required AFFILIATE_REF_URL "Реферальная ссылка 1win (https://...)"
  validate_https_url "$AFFILIATE_REF_URL" || fail "Реф. ссылка должна начинаться с https://"
  prompt_required AFFILIATE_PROMO_CODE "Промокод 1win"

  echo ""
  echo -e "${BOLD}Шаг 7. Tribute (безлимит) — опционально${NC}"
  echo "Если пока не настраиваете оплату — нажмите Enter на всех полях."
  prompt_optional TRIBUTE_API_KEY "Tribute API Key" ""
  prompt_optional TRIBUTE_SHOP_ID "Tribute Shop ID" ""
  prompt_optional TRIBUTE_WEBHOOK_SECRET "Tribute Webhook Secret" ""
  prompt_optional UNLIMITED_PRICE_AMOUNT "Цена безлимита (копейки/руб)" "4900"

  if [[ -n "${TRIBUTE_API_KEY:-}" ]]; then
    TRIBUTE_ENABLED="true"
    UNLIMITED_ENABLED="true"
  else
    TRIBUTE_ENABLED="false"
    UNLIMITED_ENABLED="false"
  fi

  prompt_optional LETSENCRYPT_EMAIL "Email для SSL (Let's Encrypt)" "admin@${BASE_DOMAIN}"
  prompt_optional SUPPORT_URL "Ссылка на поддержку" "https://t.me/${BOT_USERNAME:-support}"

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

  docker compose -f "${INSTALL_DIR}/docker-compose.yml" exec -T \
    -e CHANNEL_ID -e CHANNEL_URL -e REPORTS_CHANNEL_ID \
    -e AFFILIATE_REF_URL -e AFFILIATE_PROMO_CODE \
    -e TRIBUTE_API_KEY -e TRIBUTE_SHOP_ID -e TRIBUTE_WEBHOOK_SECRET \
    -e TRIBUTE_ENABLED -e UNLIMITED_ENABLED \
    -e UNLIMITED_PRICE_AMOUNT -e UNLIMITED_PRICE_CURRENCY \
    -e SUPPORT_URL \
    backend python - <<'PY'
import asyncio, os, sys
sys.path.insert(0, "/app")
from app.core.database import async_session_factory
from app.services.settings import SettingsService

async def main():
    mapping = {
        "channel_id": os.environ.get("CHANNEL_ID", ""),
        "channel_url": os.environ.get("CHANNEL_URL", ""),
        "reports_chat_id": os.environ.get("REPORTS_CHANNEL_ID", ""),
        "support_url": os.environ.get("SUPPORT_URL", ""),
        "affiliate_ref_url": os.environ.get("AFFILIATE_REF_URL", ""),
        "affiliate_promo_code": os.environ.get("AFFILIATE_PROMO_CODE", ""),
        "tribute_api_key": os.environ.get("TRIBUTE_API_KEY", ""),
        "tribute_shop_id": os.environ.get("TRIBUTE_SHOP_ID", ""),
        "tribute_webhook_secret": os.environ.get("TRIBUTE_WEBHOOK_SECRET", ""),
        "tribute_enabled": os.environ.get("TRIBUTE_ENABLED", "false"),
        "unlimited_enabled": os.environ.get("UNLIMITED_ENABLED", "false"),
        "unlimited_price_amount": os.environ.get("UNLIMITED_PRICE_AMOUNT", "4900"),
        "unlimited_price_currency": os.environ.get("UNLIMITED_PRICE_CURRENCY", "rub"),
    }
    async with async_session_factory() as session:
        svc = SettingsService(session)
        for k, v in mapping.items():
            if v:
                await svc.set(k, str(v))
        await session.commit()
    print("OK")

asyncio.run(main())
PY
  ok "Настройки приложения сохранены"
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
