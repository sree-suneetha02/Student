#!/bin/bash

PASS=0
FAIL=0

run_section() {
    echo ""
    echo "════════════════════════════════════════"
    echo "  $1"
    echo "════════════════════════════════════════"
}

# ── Python ────────────────────────────────────────────────────
run_section "Python (pytest) — 31 tests"
cd "$(dirname "$0")/python"
python3 -m pytest test_app.py -v 2>&1
if [ $? -eq 0 ]; then
    echo "✔  Python: ALL PASSED"
    PASS=$((PASS + 1))
else
    echo "✘  Python: SOME FAILED"
    FAIL=$((FAIL + 1))
fi

# ── Node.js ───────────────────────────────────────────────────
run_section "Node.js (Jest) — 31 tests"
cd "$(dirname "$0")/nodejs"
npm test 2>&1
if [ $? -eq 0 ]; then
    echo "✔  Node.js: ALL PASSED"
    PASS=$((PASS + 1))
else
    echo "✘  Node.js: SOME FAILED"
    FAIL=$((FAIL + 1))
fi

# ── Go ────────────────────────────────────────────────────────
run_section "Go (testing) — 31 tests"
cd "$(dirname "$0")/golang"
go test -v ./... 2>&1
if [ $? -eq 0 ]; then
    echo "✔  Go: ALL PASSED"
    PASS=$((PASS + 1))
else
    echo "✘  Go: SOME FAILED"
    FAIL=$((FAIL + 1))
fi

# ── Summary ───────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════"
echo "  SUMMARY"
echo "════════════════════════════════════════"
echo "  Passed: $PASS / 3 suites"
echo "  Failed: $FAIL / 3 suites"
echo "════════════════════════════════════════"

[ $FAIL -eq 0 ] && exit 0 || exit 1
