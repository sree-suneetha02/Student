#!/bin/bash
# ================================================================
#  Student API - Bash Test Suite (18 test cases × 3 backends)
#  Covers: health, CRUD, validation errors, 404s, 409 conflicts
#
#  Usage:
#    chmod +x test_suite.sh
#    ./test_suite.sh                  # all 3 backends
#    ./test_suite.sh python           # Python only (port 5015)
#    ./test_suite.sh nodejs           # Node.js only (port 5016)
#    ./test_suite.sh golang           # Go only (port 5017)
# ================================================================

# ── Colors ───────────────────────────────────────────────────
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ── Global counters ──────────────────────────────────────────
PASS=0
FAIL=0
SKIP=0
TOTAL=0

# ── assert HTTP status ────────────────────────────────────────
assert_status() {
  local name="$1" expected="$2" actual="$3"
  TOTAL=$((TOTAL + 1))
  if [[ "$actual" == "$expected" ]]; then
    printf "  ${GREEN}✓ PASS${NC}  %-42s HTTP %s\n" "$name" "$actual"
    PASS=$((PASS + 1))
  else
    printf "  ${RED}✗ FAIL${NC}  %-42s Expected=%s  Got=%s\n" "$name" "$expected" "$actual"
    FAIL=$((FAIL + 1))
  fi
}

# ── curl helpers ─────────────────────────────────────────────
curl_status() {
  local method="$1" url="$2" data="${3:-}"
  if [[ -n "$data" ]]; then
    curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 \
      -X "$method" "$url" -H "Content-Type: application/json" -d "$data" 2>/dev/null
  else
    curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 \
      -X "$method" "$url" 2>/dev/null
  fi
}

curl_body() {
  local method="$1" url="$2" data="${3:-}"
  if [[ -n "$data" ]]; then
    curl -s --connect-timeout 3 \
      -X "$method" "$url" -H "Content-Type: application/json" -d "$data" 2>/dev/null
  else
    curl -s --connect-timeout 3 -X "$method" "$url" 2>/dev/null
  fi
}

# ── extract "id" from JSON response ──────────────────────────
extract_id() {
  echo "$1" | python3 -c \
    "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null \
  || echo "$1" | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*'
}

# ── check if backend is reachable ────────────────────────────
is_running() {
  local code
  code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 "$1/health" 2>/dev/null)
  [[ "$code" == "200" ]]
}

# ── cleanup: delete every student in the backend ─────────────
cleanup() {
  local base="$1"
  local ids
  ids=$(curl_body "GET" "$base/students" | python3 -c \
    "import sys,json
try:
  for s in json.load(sys.stdin): print(s.get('id',''))
except: pass" 2>/dev/null)
  for sid in $ids; do
    [[ -n "$sid" ]] && curl -s -o /dev/null -X DELETE "$base/students/$sid" 2>/dev/null
  done
}

# ================================================================
#  run_tests  —  runs all 18 test cases against one backend
# ================================================================
run_tests() {
  local name="$1" base="$2"

  printf "\n${BOLD}${CYAN}┌─────────────────────────────────────────────┐${NC}\n"
  printf "${BOLD}${CYAN}│  %-44s│${NC}\n" "$name  ($base)"
  printf "${BOLD}${CYAN}└─────────────────────────────────────────────┘${NC}\n"

  if ! is_running "$base"; then
    printf "  ${YELLOW}⚠ SKIP${NC}  Server not running — start it first.\n"
    SKIP=$((SKIP + 18))
    return
  fi

  cleanup "$base"

  # ── TC01  Health check ────────────────────────────────────
  s=$(curl_status "GET" "$base/health")
  assert_status "TC01  GET /health" "200" "$s"

  # ── TC02  Get all students (starts empty) ─────────────────
  s=$(curl_status "GET" "$base/students")
  assert_status "TC02  GET /students (empty)" "200" "$s"

  # ── TC03  Create valid student ────────────────────────────
  BODY=$(curl_body "POST" "$base/students" \
    '{"name":"Alice","age":22,"email":"alice@test.com"}')
  s=$(curl_status "POST" "$base/students" \
    '{"name":"Alice","age":22,"email":"alice@test.com"}')
  assert_status "TC03  POST /students (valid)" "201" "$s"
  ALICE_ID=$(extract_id "$BODY")

  # ── TC04  Get student by valid ID ─────────────────────────
  if [[ -n "$ALICE_ID" ]]; then
    s=$(curl_status "GET" "$base/students/$ALICE_ID")
    assert_status "TC04  GET /students/$ALICE_ID (found)" "200" "$s"
  else
    printf "  ${YELLOW}⚠ SKIP${NC}  TC04 — could not extract created student ID\n"
    SKIP=$((SKIP + 1))
  fi

  # ── TC05  Get student by non-existent ID ──────────────────
  s=$(curl_status "GET" "$base/students/99999")
  assert_status "TC05  GET /students/99999 (not found)" "404" "$s"

  # ── TC06  Create — missing name ───────────────────────────
  s=$(curl_status "POST" "$base/students" \
    '{"age":20,"email":"noname@test.com"}')
  assert_status "TC06  POST /students (missing name)" "400" "$s"

  # ── TC07  Create — age below 15 ──────────────────────────
  s=$(curl_status "POST" "$base/students" \
    '{"name":"Kid","age":10,"email":"kid@test.com"}')
  assert_status "TC07  POST /students (age < 15)" "400" "$s"

  # ── TC08  Create — age above 100 ─────────────────────────
  s=$(curl_status "POST" "$base/students" \
    '{"name":"Elder","age":150,"email":"elder@test.com"}')
  assert_status "TC08  POST /students (age > 100)" "400" "$s"

  # ── TC09  Create — invalid email format ──────────────────
  s=$(curl_status "POST" "$base/students" \
    '{"name":"Dave","age":25,"email":"not-an-email"}')
  assert_status "TC09  POST /students (invalid email)" "400" "$s"

  # ── TC10  Create — empty body ─────────────────────────────
  s=$(curl_status "POST" "$base/students" '{}')
  assert_status "TC10  POST /students (empty body)" "400" "$s"

  # ── TC11  Create — missing age ────────────────────────────
  s=$(curl_status "POST" "$base/students" \
    '{"name":"Eve","email":"eve@test.com"}')
  assert_status "TC11  POST /students (missing age)" "400" "$s"

  # ── Create a second student (needed for duplicate-email tests)
  curl_body "POST" "$base/students" \
    '{"name":"Bob","age":28,"email":"bob@test.com"}' > /dev/null

  # ── TC12  Create — duplicate email ───────────────────────
  s=$(curl_status "POST" "$base/students" \
    '{"name":"Alice2","age":23,"email":"alice@test.com"}')
  assert_status "TC12  POST /students (duplicate email)" "409" "$s"

  # ── TC13  Update — valid fields ───────────────────────────
  if [[ -n "$ALICE_ID" ]]; then
    s=$(curl_status "PUT" "$base/students/$ALICE_ID" \
      '{"name":"Alice Updated","age":24}')
    assert_status "TC13  PUT /students/$ALICE_ID (valid)" "200" "$s"
  else
    printf "  ${YELLOW}⚠ SKIP${NC}  TC13 — no student ID\n"
    SKIP=$((SKIP + 1))
  fi

  # ── TC14  Update — non-existent ID ───────────────────────
  s=$(curl_status "PUT" "$base/students/99999" '{"name":"Ghost"}')
  assert_status "TC14  PUT /students/99999 (not found)" "404" "$s"

  # ── TC15  Update — duplicate email ───────────────────────
  if [[ -n "$ALICE_ID" ]]; then
    s=$(curl_status "PUT" "$base/students/$ALICE_ID" \
      '{"email":"bob@test.com"}')
    assert_status "TC15  PUT /students/:id (duplicate email)" "409" "$s"
  else
    printf "  ${YELLOW}⚠ SKIP${NC}  TC15 — no student ID\n"
    SKIP=$((SKIP + 1))
  fi

  # ── TC16  Delete — success ────────────────────────────────
  if [[ -n "$ALICE_ID" ]]; then
    s=$(curl_status "DELETE" "$base/students/$ALICE_ID")
    assert_status "TC16  DELETE /students/$ALICE_ID (success)" "200" "$s"
  else
    printf "  ${YELLOW}⚠ SKIP${NC}  TC16 — no student ID\n"
    SKIP=$((SKIP + 1))
  fi

  # ── TC17  Delete — non-existent ID ───────────────────────
  s=$(curl_status "DELETE" "$base/students/99999")
  assert_status "TC17  DELETE /students/99999 (not found)" "404" "$s"

  # ── TC18  Get all students (after inserts) ────────────────
  s=$(curl_status "GET" "$base/students")
  assert_status "TC18  GET /students (with data)" "200" "$s"
}

# ================================================================
#  Entry point
# ================================================================
printf "${BOLD}${BLUE}"
printf "╔══════════════════════════════════════════════════╗\n"
printf "║     Student API — Bash Test Suite  (curl)        ║\n"
printf "║     18 test cases × 3 backends = 54 tests        ║\n"
printf "╚══════════════════════════════════════════════════╝\n"
printf "${NC}"

FILTER="${1:-all}"

case "$FILTER" in
  python) run_tests "Python / Flask"    "http://localhost:5015" ;;
  nodejs) run_tests "Node.js / Express" "http://localhost:5016" ;;
  golang) run_tests "Go / Gin"          "http://localhost:5017" ;;
  *)
    run_tests "Python / Flask"    "http://localhost:5015"
    run_tests "Node.js / Express" "http://localhost:5016"
    run_tests "Go / Gin"          "http://localhost:5017"
    ;;
esac

# ── Summary ───────────────────────────────────────────────────
printf "\n${BOLD}${BLUE}════════════════ SUMMARY ════════════════${NC}\n"
printf "  ${GREEN}%-8s${NC} %d\n" "PASS"  "$PASS"
printf "  ${RED}%-8s${NC} %d\n"   "FAIL"  "$FAIL"
printf "  ${YELLOW}%-8s${NC} %d\n" "SKIP"  "$SKIP"
printf "  %-8s %d\n"               "TOTAL" "$TOTAL"
printf "${BOLD}${BLUE}════════════════════════════════════════${NC}\n"

if [[ "$FAIL" -gt 0 ]]; then
  printf "${RED}${BOLD}✗  Some tests failed.${NC}\n"
  exit 1
elif [[ "$SKIP" -gt 0 ]]; then
  printf "${YELLOW}${BOLD}⚠  Tests passed but some were skipped (start all backends).${NC}\n"
else
  printf "${GREEN}${BOLD}✓  All tests passed!${NC}\n"
fi
