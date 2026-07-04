#!/usr/bin/env python3
"""token-lean read guard (PreToolUse: Read).

Denies re-reading a file that is already in context and unchanged on disk.
Small files are exempt; a deliberate immediate retry is allowed, so it
never hard-blocks. Fails open on any error.
"""
import hashlib
import json
import os
import sys
import tempfile

SMALL_FILE_BYTES = 2048  # re-reading tiny files costs less than the friction


def state_path(session_id: str) -> str:
    key = hashlib.sha1(session_id.encode()).hexdigest()[:12]
    return os.path.join(tempfile.gettempdir(), f"token-lean-{key}.json")


def load_state(path: str) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(path: str, state: dict) -> None:
    try:
        with open(path, "w") as f:
            json.dump(state, f)
    except Exception:
        pass


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        },
    }))
    sys.exit(0)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # fail open

    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path")
    if not file_path:
        sys.exit(0)

    # Targeted partial reads are always fine.
    if tool_input.get("offset") is not None or tool_input.get("limit") is not None:
        sys.exit(0)

    try:
        st = os.stat(file_path)
        sig = f"{st.st_mtime_ns}:{st.st_size}"
    except OSError:
        sys.exit(0)  # missing file: let the tool report it

    if st.st_size < SMALL_FILE_BYTES:
        sys.exit(0)

    session_id = str(payload.get("session_id", "default"))
    spath = state_path(session_id)
    state = load_state(spath)
    reads = state.setdefault("reads", {})
    denied = state.setdefault("read_denied", {})

    prev = reads.get(file_path)
    if prev == sig:
        if denied.get(file_path):
            # Second attempt: deliberate — allow and reset.
            denied.pop(file_path, None)
            save_state(spath, state)
            sys.exit(0)
        denied[file_path] = 1
        save_state(spath, state)
        deny(
            f"token-lean: '{os.path.basename(file_path)}' was already read this "
            "session and is unchanged on disk. Use the version already in context, "
            "or Grep for the specific section and Read with offset/limit. "
            "If a full re-read is truly needed, repeat the same Read call."
        )

    reads[file_path] = sig
    denied.pop(file_path, None)
    save_state(spath, state)
    sys.exit(0)


if __name__ == "__main__":
    main()
