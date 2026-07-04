# token-lean

One plugin that makes coding agents cheaper and sharper: fewer tokens read, fewer tokens written, correct minimal code, terse answers. It weaves together the core ideas of the token-optimization ecosystem — terse output (Caveman-style), a minimal-code decision ladder, verbose-command compression (RTK-style), and context hygiene — into a single coherent working mode, so you don't need five plugins.

Works with **Claude Code** natively (skill + hooks + subagent + command) and with **Codex, Cursor, Copilot, or any AGENTS.md-aware agent** via the included portable rules file.

## Components

**Skill: `token-efficiency`** — three pillars applied in order:

1. *Read less* — targeted reads, terse command flags, subagent isolation, early compaction
2. *Write less* — a 5-rung decision ladder before writing any code (delete > reuse > stdlib > one-liner > minimal new code)
3. *Say less* — answer-first, no narration, no filler

Detailed rationale and patterns live in [skills/token-efficiency/references/playbook.md](skills/token-efficiency/references/playbook.md).

**Agent: `scout`** — a cheap (Haiku-powered), read-only exploration subagent. Repo-wide searches and log forensics run inside it; only the conclusion (≤15 lines) returns to the main context.

**Command: `/token-lean:lean`** — flips the current session into lean mode explicitly.

**Hooks (all fail open — any error means the tool call proceeds normally):**

- `read_guard.py` (PreToolUse: Read) — denies re-reading a file already in context and unchanged on disk. Files under 2 KB are exempt; repeating the identical Read overrides, so it never hard-blocks.
- `bash_guard.py` (PreToolUse: Bash) — intercepts known-verbose commands (`git status`, bare `git log`/`git diff`/`git show`, `cat <file>`, `grep -r`, `find -name`, unquieted `pytest` (incl. `python3 -m pytest` / `uv run pytest`), `ls -la [path]`, `npm ls`, `npm test`, `pip list`) and suggests the terse equivalent. Repeating the identical command overrides.
- `compact_reset.py` (PreCompact) — clears the read-guard's memory before compaction, since compacted context no longer contains earlier file reads.

**Portable rules: [AGENTS.md](AGENTS.md)** — the same discipline as a plain instructions file for non-Claude agents. Copy it into a repo root, or to `~/.codex/AGENTS.md` for Codex globally.

## Install

### Claude Code (as a plugin)

```
/plugin marketplace add EswarSk/token-lean
/plugin install token-lean@token-lean
```

### Codex / Cursor / anything else

Copy [AGENTS.md](AGENTS.md) into your repo root (or merge it into your existing AGENTS.md / .cursorrules). Done — no hooks, no runtime, just rules.

## Usage

- Say "save tokens", "token diet", "be token efficient", or "optimize context" — or run `/token-lean:lean` — to load the skill explicitly.
- Hooks are active automatically once the plugin is installed.
- For always-on behavior in a project, add one line to that project's CLAUDE.md: `Follow the token-efficiency skill.`

## Setup requirements

Only `python3` on PATH. Per-session state is kept in a small temp file; nothing is sent anywhere.

## Tuning

- Add/remove command rewrite rules: edit `RULES` in [hooks/scripts/bash_guard.py](hooks/scripts/bash_guard.py).
- Change the small-file exemption: edit `SMALL_FILE_BYTES` in [hooks/scripts/read_guard.py](hooks/scripts/read_guard.py).
- Disable a hook: remove its entry from [hooks/hooks.json](hooks/hooks.json).

## Testing

```
python3 tests/test_hooks.py
```

## License

MIT
