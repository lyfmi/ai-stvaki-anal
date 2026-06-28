#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=../lib/common.sh
source "${ROOT}/lib/common.sh"
# shellcheck source=../lib/env.sh
source "${ROOT}/lib/env.sh"
# shellcheck source=lib/assert.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib/assert.sh"

failures=0

test_write_env_dry_run() {
  DRY_RUN=1
  APP_DOMAIN="tgbot.test.example"
  BOT_TOKEN="8000562992:AAHbbUOplW6gpOsZmiMQepKUgoHYwVVDYxU"
  ADMIN_TELEGRAM_ID="123456789"
  REPORTS_CHANNEL_ID="-1001111111111"
  TRIBUTE_API_KEY=""

  local tmp
  tmp="$(mktemp)"
  write_env_file "$tmp"
  # dry-run does not write file
  if [[ -f "$tmp" ]] && [[ -s "$tmp" ]]; then
    echo "unexpected file content in dry-run" >&2
    return 1
  fi
  rm -f "$tmp"
  return 0
}

test_write_env_content() {
  DRY_RUN=0
  APP_DOMAIN="tgbot.test.example"
  BOT_TOKEN="8000562992:AAHbbUOplW6gpOsZmiMQepKUgoHYwVVDYxU"
  ADMIN_TELEGRAM_ID="123456789"
  REPORTS_CHANNEL_ID="-1001111111111"
  TRIBUTE_API_KEY=""

  local tmp
  tmp="$(mktemp)"
  write_env_file "$tmp"

  grep -q "BOT_TOKEN=${BOT_TOKEN}" "$tmp" || return 1
  grep -q "PUBLIC_BASE_URL=https://tgbot.test.example" "$tmp" || return 1
  grep -q "NOUS_API_KEY=${NOUS_API_KEY_DEFAULT}" "$tmp" || return 1
  grep -q "SEARCH_PROVIDER=searxng" "$tmp" || return 1
  grep -q "ADMIN_TELEGRAM_IDS=123456789" "$tmp" || return 1
  rm -f "$tmp"
  return 0
}

test_render_nginx() {
  DRY_RUN=0
  local tmp out
  tmp="$(mktemp)"
  out="$(mktemp)"
  echo 'server_name __DOMAIN__;' >"$tmp"
  render_nginx_config "$tmp" "$out" "tgbot.example.ru"
  grep -q "server_name tgbot.example.ru;" "$out" || return 1
  rm -f "$tmp" "$out"
  return 0
}

echo "=== test_env.sh ==="
if test_write_env_dry_run; then echo "  OK  write_env dry-run"; else echo "  FAIL write_env dry-run"; ((failures++)) || true; fi
if test_write_env_content; then echo "  OK  write_env content"; else echo "  FAIL write_env content"; ((failures++)) || true; fi
if test_render_nginx; then echo "  OK  render nginx"; else echo "  FAIL render nginx"; ((failures++)) || true; fi

if (( failures > 0 )); then
  echo "FAILED: ${failures} case(s)"
  exit 1
fi
echo "All env tests passed."
