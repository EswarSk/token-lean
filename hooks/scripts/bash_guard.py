#!/usr/bin/env python3
"""token-lean bash guard (PreToolUse: Bash).

Denies known-verbose commands once, suggesting a terse equivalent
(RTK-style input compression). Retrying the identical command passes
through, so it never hard-blocks. Fails open on any error.
"""
import hashlib
import json
import os
import re
import sys
import tempfile

# (pattern, suggestion) — first match wins. Patterns match the *whole* command.
RULES = [
    (r"^git status\s*$",
     "Use `git status --porcelain -b` (same info, ~75% fewer tokens)."),
    (r"^git log(?!.*(--oneline|--format|--pretty|-n\b|-\d))\b.*$",
     "Use `git log --oneline -15` (add flags/paths as needed)."),
    (r"^git diff\s*$",
     "Use `git diff --stat` first, then `git diff -- <file>` for files that matter."),
    (r"^git show\s*$",
     "Use `git show --stat` first, then targeted `git show -- <file>`."),
    (r"^ls\s+-(la|al|lah|alh|l)(\s+\S+)?\s*$",
     "Use `ls -1` unless permissions/sizes are actually needed."),
    (r"^cat\s+[^|;&<>]+$",
     "Use `head -100 <file>` or the Read tool with offset/limit; "
     "full `cat` dumps the whole file into context."),
    (r"^grep\s+-[a-zA-Z]*r[a-zA-Z]*\b.*$",
     "Use the Grep tool instead of recursive grep — indexed, filtered, capped output."),
    (r"^find\s+\S+\s+-name\b.*$",
     "Use the Glob tool instead of `find -name` — faster and terser."),
    (r"^(python[0-9.]*\s+-m\s+|uv\s+run\s+)?pytest(?!.*(-q|--quiet))\b.*$",
     "Add `-q` to pytest (pass/fail summary instead of full dots and headers)."),
    (r"^npm (ls|list)\s*$",
     "Use `npm ls --depth=0` to avoid dumping the full dependency tree."),
    (r"^pip list\s*$",
     "Use `pip list 2>/dev/null | head -30` or grep for the package you need."),
    (r"^npm test\s*$",
     "Prefer the project's quiet test script or pipe: `npm test 2>&1 | tail -30`."),
]


def state_path(session_id: str) -> str:
    key = hashlib.sha1(session_id.encode()).hexdigest()[:12]
    return os.path.join(tempfile.gettempdir(), f"token-lean-{key}.json")


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # fail open

    command = ((payload.get("tool_input") or {}).get("command") or "").strip()
    if not command:
        sys.exit(0)

    suggestion = None
    for pattern, hint in RULES:
        if re.match(pattern, command):
            suggestion = hint
            break
    if not suggestion:
        sys.exit(0)

    session_id = str(payload.get("session_id", "default"))
    spath = state_path(session_id)
    try:
        with open(spath) as f:
            state = json.load(f)
    except Exception:
        state = {}
    denied = state.setdefault("bash_denied", {})
    chash = hashlib.sha1(command.encode()).hexdigest()[:16]

    if denied.get(chash):
        sys.exit(0)  # deliberate retry — allow

    denied[chash] = 1
    try:
        with open(spath, "w") as f:
            json.dump(state, f)
    except Exception:
        pass

    reason = (f"token-lean: verbose command intercepted. {suggestion} "
              "Repeat the identical command to run it anyway.")
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        },
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
