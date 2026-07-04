#!/usr/bin/env python3
"""token-lean compact reset (PreCompact).

After compaction, earlier file reads are no longer in context, so the
read guard's memory would wrongly deny legitimate re-reads. Clear it.
Fails open on any error.
"""
import hashlib
import json
import os
import sys
import tempfile


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    session_id = str(payload.get("session_id", "default"))
    key = hashlib.sha1(session_id.encode()).hexdigest()[:12]
    path = os.path.join(tempfile.gettempdir(), f"token-lean-{key}.json")
    try:
        with open(path) as f:
            state = json.load(f)
        state.pop("reads", None)
        state.pop("read_denied", None)
        with open(path, "w") as f:
            json.dump(state, f)
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
