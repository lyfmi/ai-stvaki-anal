#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=../lib/validate.sh
source "${ROOT}/lib/validate.sh"
# shellcheck source=lib/assert.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib/assert.sh"

failures=0

run_case() {
  local name="$1"
  shift
  if "$@"; then
    echo "  OK  ${name}"
  else
    echo "  FAIL ${name}"
    ((failures++)) || true
  fi
}

test_normalize_domain() {
  assert_eq "example.ru" "$(normalize_domain "https://Example.RU/path")"
  assert_eq "tgbot.example.ru" "$(normalize_domain " tgbot.example.ru ")"
}

test_suggest_subdomain() {
  assert_eq "tgbot.example.ru" "$(suggest_subdomain "example.ru" "tgbot")"
}

test_validate_bot_token() {
  assert_ok "validate_bot_token '8000562992:AAHbbUOplW6gpOsZmiMQepKUgoHYwVVDYxU'"
  assert_fail "validate_bot_token 'bad-token'"
  assert_fail "validate_bot_token ''"
}

test_validate_telegram_id() {
  assert_ok "validate_telegram_id '7649494487'"
  assert_ok "validate_telegram_id '-1003994637971'"
  assert_fail "validate_telegram_id 'abc'"
}

test_validate_urls() {
  assert_ok "validate_https_url 'https://one-vv53243.com/betting'"
  assert_fail "validate_https_url 'http://insecure.com'"
  assert_ok "validate_channel_url 'https://t.me/mychannel'"
  assert_fail "validate_channel_url 'https://example.com/x'"
}

test_validate_domain() {
  assert_ok "validate_domain 'tgbot.example.ru'"
  assert_fail "validate_domain 'bad domain!'"
}

echo "=== test_validate.sh ==="
run_case normalize_domain test_normalize_domain
run_case suggest_subdomain test_suggest_subdomain
run_case validate_bot_token test_validate_bot_token
run_case validate_telegram_id test_validate_telegram_id
run_case validate_urls test_validate_urls
run_case validate_domain test_validate_domain

if (( failures > 0 )); then
  echo "FAILED: ${failures} case(s)"
  exit 1
fi
echo "All validate tests passed."
