#!/usr/bin/env bash
# shellcheck shell=bash

wait_for_dns() {
  local domain="$1"
  local expected_ip="$2"
  local max_attempts="${3:-30}"
  local sleep_sec="${4:-30}"
  local attempt=0
  local resolved=""

  info "Ожидаем привязку домена ${domain} к серверу ${expected_ip} (до $(( max_attempts * sleep_sec / 60 )) мин.)"

  while (( attempt < max_attempts )); do
    resolved="$(dig +short A "$domain" 2>/dev/null | grep -E '^[0-9.]+$' | tail -1 || true)"
    if [[ "$resolved" == "$expected_ip" ]]; then
      ok "Домен привязан: ${domain} → ${resolved}"
      return 0
    fi
    if [[ -n "$resolved" ]]; then
      warn "Сейчас ${domain} указывает на ${resolved}, нужен ${expected_ip} — ждём обновления DNS (попытка $((attempt + 1))/${max_attempts})"
    else
      warn "Домен пока не виден — проверьте A-запись в личном кабинете регистратора (попытка $((attempt + 1))/${max_attempts})"
    fi
    if [[ "$DRY_RUN" == "1" ]]; then
      ok "[dry-run] DNS check skipped"
      return 0
    fi
    sleep "$sleep_sec"
    ((attempt++))
  done

  fail "Домен не привязался за 15 минут. Проверьте A-запись в личном кабинете домена (Reg.ru, Timeweb и т.п.) и запустите скрипт снова."
}
