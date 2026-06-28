#!/usr/bin/env bash
# shellcheck shell=bash

wait_for_dns() {
  local domain="$1"
  local expected_ip="$2"
  local max_attempts="${3:-30}"
  local sleep_sec="${4:-30}"
  local attempt=0
  local resolved=""

  info "Ожидаем DNS A-запись для ${domain} → ${expected_ip} (до $(( max_attempts * sleep_sec / 60 )) мин.)"

  while (( attempt < max_attempts )); do
    resolved="$(dig +short A "$domain" 2>/dev/null | grep -E '^[0-9.]+$' | tail -1 || true)"
    if [[ "$resolved" == "$expected_ip" ]]; then
      ok "DNS готов: ${domain} → ${resolved}"
      return 0
    fi
    if [[ -n "$resolved" ]]; then
      warn "Сейчас ${domain} → ${resolved}, ожидаем ${expected_ip} (попытка $((attempt + 1))/${max_attempts})"
    else
      warn "Запись ещё не видна (попытка $((attempt + 1))/${max_attempts})"
    fi
    if [[ "$DRY_RUN" == "1" ]]; then
      ok "[dry-run] DNS check skipped"
      return 0
    fi
    sleep "$sleep_sec"
    ((attempt++))
  done

  fail "DNS не обновился за отведённое время. Проверьте A-запись у регистратора."
}
