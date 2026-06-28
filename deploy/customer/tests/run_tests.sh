#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================"
echo " AI Bet Bot Installer — test suite"
echo "========================================"

bash "${DIR}/test_syntax.sh"
bash "${DIR}/test_validate.sh"
bash "${DIR}/test_env.sh"

echo ""
echo "All installer tests passed."
