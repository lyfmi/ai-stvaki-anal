#!/usr/bin/env bash
# shellcheck shell=bash

validate_domain() {
  local domain="$1"
  [[ "$domain" =~ ^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$ ]]
}

validate_bot_token() {
  local token="$1"
  [[ "$token" =~ ^[0-9]{8,12}:[A-Za-z0-9_-]{30,}$ ]]
}

validate_telegram_id() {
  local id="$1"
  [[ "$id" =~ ^-?[0-9]{5,20}$ ]]
}

validate_https_url() {
  local url="$1"
  [[ "$url" =~ ^https://[^[:space:]]+$ ]]
}

validate_channel_url() {
  local url="$1"
  [[ "$url" =~ ^https://t\.me/[^[:space:]/]+/?$ ]]
}

normalize_domain() {
  local input="$1"
  input="$(echo "$input" | tr '[:upper:]' '[:lower:]' | xargs)"
  input="${input#https://}"
  input="${input#http://}"
  input="${input%%/*}"
  echo "$input"
}

suggest_subdomain() {
  local base_domain="$1"
  local prefix="${2:-tgbot}"
  echo "${prefix}.${base_domain}"
}
