#!/usr/bin/env python3
"""
Student API — Dynamic curl Command Generator
Generates and optionally executes curl commands for all 18 test cases.

Usage:
    python3 generate_curl.py                      # print commands for all backends
    python3 generate_curl.py --backend python     # Python (5015) only
    python3 generate_curl.py --backend nodejs     # Node.js (5016) only
    python3 generate_curl.py --backend golang     # Go (5017) only
    python3 generate_curl.py --run                # execute commands + verify status codes
    python3 generate_curl.py --run --backend python
"""

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Optional

# ── ANSI colors ───────────────────────────────────────────────
GREEN  = "\033[0;32m"
RED    = "\033[0;31m"
YELLOW = "\033[1;33m"
CYAN   = "\033[0;36m"
BOLD   = "\033[1m"
NC     = "\033[0m"


# ── Backend registry ──────────────────────────────────────────
BACKENDS = {
    "python": ("Python / Flask",    "http://localhost:5015"),
    "nodejs": ("Node.js / Express", "http://localhost:5016"),
    "golang": ("Go / Gin",          "http://localhost:5017"),
}


@dataclass
class TestCase:
    id: str
    name: str
    method: str
    endpoint: str
    body: Optional[dict] = None
    expected_status: int = 200
    description: str = ""

    def url(self, base: str) -> str:
        return f"{base}{self.endpoint}"

    def curl_command(self, base: str) -> str:
        parts = ["curl", "-s", "-o", "/dev/null", "-w", '"%{http_code}"',
                 "--connect-timeout", "3",
                 "-X", self.method,
                 f'"{self.url(base)}"']
        if self.body is not None:
            parts += ["-H", '"Content-Type: application/json"',
                      "-d", f"'{json.dumps(self.body)}'"]
        return " ".join(parts)

    def curl_with_body_command(self, base: str) -> str:
        """Variant that returns the full response body (for ID extraction)."""
        parts = ["curl", "-s", "--connect-timeout", "3",
                 "-X", self.method,
                 f'"{self.url(base)}"']
        if self.body is not None:
            parts += ["-H", '"Content-Type: application/json"',
                      "-d", f"'{json.dumps(self.body)}'"]
        return " ".join(parts)


# ── Test case definitions ─────────────────────────────────────
# Note: TC03 creates a student whose ID is used by TC04/TC13/TC15/TC16.
#       TC12 requires that a second student (bob) was inserted first.
#       The runner handles this sequencing automatically.

TEST_CASES: list[TestCase] = [
    TestCase(
        id="TC01", name="Health check",
        method="GET", endpoint="/health",
        expected_status=200,
        description="Server must return {status: healthy}",
    ),
    TestCase(
        id="TC02", name="GET /students (empty)",
        method="GET", endpoint="/students",
        expected_status=200,
        description="Returns an empty array when no students exist",
    ),
    TestCase(
        id="TC03", name="POST /students (valid)",
        method="POST", endpoint="/students",
        body={"name": "Alice", "age": 22, "email": "alice@test.com"},
        expected_status=201,
        description="Creates a student; response contains the new ID",
    ),
    TestCase(
        id="TC04", name="GET /students/:id (found)",
        method="GET", endpoint="/students/{alice_id}",
        expected_status=200,
        description="Retrieves the student created in TC03",
    ),
    TestCase(
        id="TC05", name="GET /students/99999 (not found)",
        method="GET", endpoint="/students/99999",
        expected_status=404,
        description="Non-existent ID returns 404",
    ),
    TestCase(
        id="TC06", name="POST /students (missing name)",
        method="POST", endpoint="/students",
        body={"age": 20, "email": "noname@test.com"},
        expected_status=400,
        description="Validation: name is required",
    ),
    TestCase(
        id="TC07", name="POST /students (age < 15)",
        method="POST", endpoint="/students",
        body={"name": "Kid", "age": 10, "email": "kid@test.com"},
        expected_status=400,
        description="Validation: age must be >= 15",
    ),
    TestCase(
        id="TC08", name="POST /students (age > 100)",
        method="POST", endpoint="/students",
        body={"name": "Elder", "age": 150, "email": "elder@test.com"},
        expected_status=400,
        description="Validation: age must be <= 100",
    ),
    TestCase(
        id="TC09", name="POST /students (invalid email)",
        method="POST", endpoint="/students",
        body={"name": "Dave", "age": 25, "email": "not-an-email"},
        expected_status=400,
        description="Validation: email must match RFC format",
    ),
    TestCase(
        id="TC10", name="POST /students (empty body)",
        method="POST", endpoint="/students",
        body={},
        expected_status=400,
        description="Validation: all fields are required",
    ),
    TestCase(
        id="TC11", name="POST /students (missing age)",
        method="POST", endpoint="/students",
        body={"name": "Eve", "email": "eve@test.com"},
        expected_status=400,
        description="Validation: age is required",
    ),
    TestCase(
        id="TC12", name="POST /students (duplicate email)",
        method="POST", endpoint="/students",
        body={"name": "Alice2", "age": 23, "email": "alice@test.com"},
        expected_status=409,
        description="Unique constraint: alice@test.com already exists",
    ),
    TestCase(
        id="TC13", name="PUT /students/:id (valid update)",
        method="PUT", endpoint="/students/{alice_id}",
        body={"name": "Alice Updated", "age": 24},
        expected_status=200,
        description="Partial update — only name and age changed",
    ),
    TestCase(
        id="TC14", name="PUT /students/99999 (not found)",
        method="PUT", endpoint="/students/99999",
        body={"name": "Ghost"},
        expected_status=404,
        description="Update on non-existent ID returns 404",
    ),
    TestCase(
        id="TC15", name="PUT /students/:id (duplicate email)",
        method="PUT", endpoint="/students/{alice_id}",
        body={"email": "bob@test.com"},
        expected_status=409,
        description="Email uniqueness enforced on update",
    ),
    TestCase(
        id="TC16", name="DELETE /students/:id (success)",
        method="DELETE", endpoint="/students/{alice_id}",
        expected_status=200,
        description="Successfully deletes the student",
    ),
    TestCase(
        id="TC17", name="DELETE /students/99999 (not found)",
        method="DELETE", endpoint="/students/99999",
        expected_status=404,
        description="Delete on non-existent ID returns 404",
    ),
    TestCase(
        id="TC18", name="GET /students (with data)",
        method="GET", endpoint="/students",
        expected_status=200,
        description="Returns remaining students after TC16 delete",
    ),
]


# ── Curl generator ────────────────────────────────────────────

def render_endpoint(endpoint: str, alice_id: int = 1) -> str:
    return endpoint.replace("{alice_id}", str(alice_id))


def generate_commands(base: str, alice_id: int = 1) -> list[str]:
    """Return one curl command string per test case."""
    commands = []
    for tc in TEST_CASES:
        ep = render_endpoint(tc.endpoint, alice_id)
        url = f"{base}{ep}"
        parts = [
            "curl", "-s", "-o", "/dev/null", "-w", '"%{http_code}"',
            "--connect-timeout", "3",
            "-X", tc.method,
            f'"{url}"',
        ]
        if tc.body is not None:
            parts += [
                "-H", '"Content-Type: application/json"',
                "-d", f"'{json.dumps(tc.body)}'",
            ]
        commands.append(" ".join(parts))
    return commands


def print_commands(backend_key: Optional[str] = None) -> None:
    targets = (
        [(backend_key, *BACKENDS[backend_key])]
        if backend_key
        else [(k, *v) for k, v in BACKENDS.items()]
    )
    for key, label, base in targets:
        print(f"\n{BOLD}{CYAN}# ── {label} ({base}) ──{NC}")
        commands = generate_commands(base)
        for tc, cmd in zip(TEST_CASES, commands):
            print(f"\n# {tc.id}: {tc.name}")
            print(f"# Expected HTTP {tc.expected_status} — {tc.description}")
            print(cmd)


# ── Runner ────────────────────────────────────────────────────

def _curl_json(method: str, url: str, body: Optional[dict]) -> tuple[int, dict]:
    cmd = ["curl", "-s", "--connect-timeout", "3", "-X", method, url]
    if body is not None:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(body)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        data = json.loads(result.stdout) if result.stdout.strip() else {}
        # get status separately
        status_cmd = ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                      "--connect-timeout", "3", "-X", method, url]
        if body is not None:
            status_cmd += ["-H", "Content-Type: application/json",
                           "-d", json.dumps(body)]
        status_result = subprocess.run(status_cmd, capture_output=True, text=True, timeout=5)
        status = int(status_result.stdout.strip()) if status_result.stdout.strip() else 0
        return status, data
    except Exception:
        return 0, {}


def _is_running(base: str) -> bool:
    try:
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             "--connect-timeout", "2", f"{base}/health"],
            capture_output=True, text=True, timeout=4,
        )
        return result.stdout.strip() == "200"
    except Exception:
        return False


def _cleanup(base: str) -> None:
    try:
        result = subprocess.run(
            ["curl", "-s", "--connect-timeout", "3", f"{base}/students"],
            capture_output=True, text=True, timeout=5,
        )
        students = json.loads(result.stdout) if result.stdout.strip() else []
        for s in students:
            sid = s.get("id")
            if sid:
                subprocess.run(
                    ["curl", "-s", "-o", "/dev/null", "-X", "DELETE",
                     f"{base}/students/{sid}"],
                    capture_output=True, timeout=5,
                )
    except Exception:
        pass


def run_tests(backend_key: Optional[str] = None) -> bool:
    targets = (
        [(backend_key, *BACKENDS[backend_key])]
        if backend_key
        else [(k, *v) for k, v in BACKENDS.items()]
    )

    total_pass = total_fail = total_skip = 0

    for key, label, base in targets:
        print(f"\n{BOLD}{CYAN}┌─────────────────────────────────────────────┐{NC}")
        print(f"{BOLD}{CYAN}│  {label:<44}│{NC}")
        print(f"{BOLD}{CYAN}│  {base:<44}│{NC}")
        print(f"{BOLD}{CYAN}└─────────────────────────────────────────────┘{NC}")

        if not _is_running(base):
            print(f"  {YELLOW}⚠ SKIP{NC}  Server not running — start it first.")
            total_skip += len(TEST_CASES)
            continue

        _cleanup(base)

        alice_id: Optional[int] = None
        passed = failed = skipped = 0

        for tc in TEST_CASES:
            # Resolve dynamic endpoint
            if "{alice_id}" in tc.endpoint:
                if alice_id is None:
                    print(f"  {YELLOW}⚠ SKIP{NC}  {tc.id}  {tc.name} — no alice_id yet")
                    skipped += 1
                    continue
                ep = tc.endpoint.replace("{alice_id}", str(alice_id))
            else:
                ep = tc.endpoint

            url = f"{base}{ep}"

            # TC12 needs bob to exist — insert him just before
            if tc.id == "TC12":
                subprocess.run(
                    ["curl", "-s", "-o", "/dev/null", "-X", "POST", f"{base}/students",
                     "-H", "Content-Type: application/json",
                     "-d", json.dumps({"name": "Bob", "age": 28, "email": "bob@test.com"})],
                    capture_output=True, timeout=5,
                )

            status, body = _curl_json(tc.method, url, tc.body)

            if status == tc.expected_status:
                print(f"  {GREEN}✓ PASS{NC}  {tc.id:<6}  {tc.name:<40}  HTTP {status}")
                passed += 1
                if tc.id == "TC03" and isinstance(body, dict):
                    alice_id = body.get("id")
            else:
                print(f"  {RED}✗ FAIL{NC}  {tc.id:<6}  {tc.name:<40}  "
                      f"Expected={tc.expected_status}  Got={status}")
                failed += 1

        total_pass += passed
        total_fail += failed
        total_skip += skipped
        print(f"\n  Backend result — Pass={passed}  Fail={failed}  Skip={skipped}")

    # ── Overall summary ──────────────────────────────────────
    print(f"\n{BOLD}════════════════ SUMMARY ════════════════{NC}")
    print(f"  {GREEN}PASS {NC}  {total_pass}")
    print(f"  {RED}FAIL {NC}  {total_fail}")
    print(f"  {YELLOW}SKIP {NC}  {total_skip}")
    print(f"  TOTAL   {total_pass + total_fail + total_skip}")
    print(f"{BOLD}════════════════════════════════════════{NC}")

    if total_fail > 0:
        print(f"{RED}{BOLD}✗  Some tests failed.{NC}")
        return False
    if total_skip > 0:
        print(f"{YELLOW}{BOLD}⚠  All run tests passed; some skipped (start backends).{NC}")
    else:
        print(f"{GREEN}{BOLD}✓  All tests passed!{NC}")
    return True


# ── CLI ───────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Student API — curl command generator & runner"
    )
    parser.add_argument(
        "--backend", choices=list(BACKENDS.keys()),
        help="Limit to one backend (default: all three)",
    )
    parser.add_argument(
        "--run", action="store_true",
        help="Execute the curl commands and verify HTTP status codes",
    )
    args = parser.parse_args()

    if args.run:
        ok = run_tests(args.backend)
        sys.exit(0 if ok else 1)
    else:
        print_commands(args.backend)


if __name__ == "__main__":
    main()
