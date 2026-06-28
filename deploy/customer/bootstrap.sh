#!/usr/bin/env bash
# Bootstrap installer — скачивается с https://cwais.ru/b9kR2xW4pQ/install.sh
# Запуск: curl -fsSL https://cwais.ru/b9kR2xW4pQ/install.sh | sudo bash

set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/lyfmi/ai-stvaki-anal.git}"
INSTALL_DIR="${INSTALL_DIR:-/opt/ai-bot-stavki}"
BRANCH="${BRANCH:-main}"

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  echo "Запустите от root: curl -fsSL https://cwais.ru/b9kR2xW4pQ/install.sh | sudo bash"
  exit 1
fi

echo "==> AI Bet Bot — подготовка системы..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq git ca-certificates curl

if [[ -d "$INSTALL_DIR/.git" ]]; then
  echo "==> Обновление репозитория в ${INSTALL_DIR}..."
  git -C "$INSTALL_DIR" fetch --depth 1 origin "$BRANCH"
  git -C "$INSTALL_DIR" reset --hard "origin/${BRANCH}"
else
  echo "==> Клонирование репозитория..."
  rm -rf "$INSTALL_DIR"
  git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
fi

exec bash "${INSTALL_DIR}/deploy/customer/install.sh" "$@"
