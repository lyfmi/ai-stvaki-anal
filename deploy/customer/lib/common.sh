#!/usr/bin/env bash
# shellcheck shell=bash
# Shared helpers for AI Bet Bot installer.

set -euo pipefail

INSTALLER_VERSION="1.0.0"
INSTALL_DIR="${INSTALL_DIR:-/opt/ai-bot-stavki}"
LOG_FILE="${LOG_FILE:-/var/log/ai-bot-stavki-install.log}"
if [[ "${EUID:-$(id -u)}" -ne 0 ]] && [[ "$LOG_FILE" == /var/log/* ]]; then
  LOG_FILE="/tmp/ai-bot-stavki-install.log"
fi

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

DRY_RUN="${DRY_RUN:-0}"

log() {
  local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $*"
  echo -e "$msg" | tee -a "$LOG_FILE"
}

info()  { log "${CYAN}INFO${NC}  $*"; }
ok()    { log "${GREEN}OK${NC}    $*"; }
warn()  { log "${YELLOW}WARN${NC}  $*"; }
fail()  { log "${RED}ERROR${NC} $*"; exit 1; }

require_root() {
  if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
    fail "Запустите установщик от root: sudo bash install.sh"
  fi
}

require_ubuntu_2404() {
  if [[ ! -f /etc/os-release ]]; then
    fail "Не удалось определить ОС. Требуется Ubuntu 24.04."
  fi
  # shellcheck disable=SC1091
  source /etc/os-release
  if [[ "${ID:-}" != "ubuntu" ]] || [[ "${VERSION_ID:-}" != "24.04" ]]; then
    warn "Ожидается Ubuntu 24.04, обнаружено: ${PRETTY_NAME:-unknown}"
    read -r -p "Продолжить всё равно? (y — да, n — выйти) [y/N]: " ans
    [[ "${ans,,}" == "y" ]] || fail "Установка прервана."
  fi
}

run_cmd() {
  if [[ "$DRY_RUN" == "1" ]]; then
    info "[dry-run] $*"
    return 0
  fi
  "$@"
}

random_hex() {
  openssl rand -hex "${1:-16}"
}

prompt_required() {
  local var_name="$1"
  local prompt_text="$2"
  local value=""
  while [[ -z "$value" ]]; do
    read -r -p "$prompt_text: " value
    value="$(echo "$value" | xargs)"
    if [[ -z "$value" ]]; then
      echo "Это поле обязательно — введите значение (подсказка в скобках выше)." >&2
    fi
  done
  printf -v "$var_name" '%s' "$value"
}

prompt_optional() {
  local var_name="$1"
  local prompt_text="$2"
  local default="${3:-}"
  local value=""
  if [[ -n "$default" ]]; then
    read -r -p "$prompt_text [$default]: " value
    value="${value:-$default}"
  else
    read -r -p "$prompt_text (Enter — пропустить, если не знаете): " value
  fi
  printf -v "$var_name" '%s' "$(echo "$value" | xargs)"
}

confirm() {
  local prompt_text="$1"
  local ans=""
  read -r -p "$prompt_text [y/N]: " ans
  [[ "${ans,,}" == "y" ]]
}

get_public_ip() {
  curl -4 -fsS --max-time 10 https://api.ipify.org 2>/dev/null \
    || curl -4 -fsS --max-time 10 https://ifconfig.me 2>/dev/null \
    || hostname -I | awk '{print $1}'
}

script_dir() {
  cd "$(dirname "${BASH_SOURCE[1]}")/.." && pwd
}
