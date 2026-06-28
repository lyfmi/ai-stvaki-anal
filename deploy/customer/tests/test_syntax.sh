#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== test_syntax.sh (bash -n + shellcheck) ==="

while IFS= read -r -d '' script; do
  bash -n "$script" || { echo "Syntax error: $script"; exit 1; }
  echo "  OK  bash -n ${script#${ROOT}/}"
done < <(find "$ROOT" -maxdepth 3 -name '*.sh' -print0)

if command -v shellcheck >/dev/null 2>&1; then
  shellcheck -x \
    "${ROOT}/install.sh" \
    "${ROOT}/bootstrap.sh" \
    "${ROOT}/lib/common.sh" \
    "${ROOT}/lib/validate.sh" \
    "${ROOT}/lib/dns.sh" \
    "${ROOT}/lib/env.sh" \
    "${ROOT}/tests/test_validate.sh" \
    "${ROOT}/tests/test_env.sh"
  echo "  OK  shellcheck"
else
  echo "  SKIP shellcheck (not installed)"
fi

echo "Syntax checks passed."
