#!/usr/bin/env bash
# Test helpers

assert_eq() {
  local expected="$1"
  local actual="$2"
  local msg="${3:-}"
  if [[ "$expected" != "$actual" ]]; then
    echo "FAIL: expected '${expected}', got '${actual}' ${msg}" >&2
    return 1
  fi
  return 0
}

assert_ok() {
  local cmd="$1"
  local msg="${2:-}"
  if eval "$cmd"; then
    return 0
  fi
  echo "FAIL: command should succeed: ${cmd} ${msg}" >&2
  return 1
}

assert_fail() {
  local cmd="$1"
  local msg="${2:-}"
  if eval "$cmd"; then
    echo "FAIL: command should fail: ${cmd} ${msg}" >&2
    return 1
  fi
  return 0
}
