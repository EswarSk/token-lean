#!/usr/bin/env python3
"""Smoke tests for token-lean hooks. Run: python3 tests/test_hooks.py"""
import json
import os
import subprocess
import sys
import tempfile
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "hooks", "scripts")
failures = []


def run(script, payload):
    p = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, script)],
        input=json.dumps(payload), capture_output=True, text=True,
    )
    out = p.stdout.strip()
    return json.loads(out) if out else None


def check(name, cond):
    print(("PASS" if cond else "FAIL"), name)
    if not cond:
        failures.append(name)


def denied(result):
    return bool(result) and result.get("hookSpecificOutput", {}).get(
        "permissionDecision") == "deny"


def bash(cmd, session):
    return run("bash_guard.py", {"session_id": session,
                                 "tool_input": {"command": cmd}})


# --- bash_guard: verbose commands denied once, retry allowed ---
s = f"t-{uuid.uuid4()}"
check("git status denied", denied(bash("git status", s)))
check("git status retry allowed", bash("git status", s) is None)
check("git log denied", denied(bash("git log", f"t-{uuid.uuid4()}")))
check("git log --oneline allowed", bash("git log --oneline -5", s) is None)
check("python3 -m pytest denied",
      denied(bash("python3 -m pytest tests/", f"t-{uuid.uuid4()}")))
check("uv run pytest denied",
      denied(bash("uv run pytest", f"t-{uuid.uuid4()}")))
check("pytest -q allowed", bash("pytest -q tests/", s) is None)
check("ls -la <path> denied", denied(bash("ls -la /tmp", f"t-{uuid.uuid4()}")))
check("cat file denied", denied(bash("cat package.json", f"t-{uuid.uuid4()}")))
check("cat | grep allowed", bash("cat f.txt | grep x", s) is None)
check("grep -rn denied", denied(bash("grep -rn TODO .", f"t-{uuid.uuid4()}")))

# --- read_guard: big file re-read denied once; small file exempt ---
big = tempfile.NamedTemporaryFile(suffix=".txt", delete=False)
big.write(b"x" * 5000)
big.close()
small = tempfile.NamedTemporaryFile(suffix=".txt", delete=False)
small.write(b"x" * 100)
small.close()

s = f"t-{uuid.uuid4()}"


def read(path, session, **extra):
    return run("read_guard.py", {"session_id": session,
                                 "tool_input": {"file_path": path, **extra}})


check("first read allowed", read(big.name, s) is None)
check("re-read denied", denied(read(big.name, s)))
check("re-read retry allowed", read(big.name, s) is None)
check("partial read allowed", read(big.name, s, offset=1, limit=10) is None)
check("small file exempt", read(small.name, s) is None
      and read(small.name, s) is None)

os.chmod(big.name, 0o644)
with open(big.name, "a") as f:
    f.write("changed")
check("re-read after change allowed", read(big.name, s) is None)

# --- compact_reset clears read state ---
run("compact_reset.py", {"session_id": s})
check("read allowed after compact", read(big.name, s) is None)

os.unlink(big.name)
os.unlink(small.name)

print(f"\n{len(failures)} failure(s)")
sys.exit(1 if failures else 0)
