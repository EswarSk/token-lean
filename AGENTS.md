# Token-Lean Rules (portable)

Copy this file into any repo root (or `~/.codex/AGENTS.md` for Codex global
config) to get token-lean behavior from Codex, Cursor, Copilot, or any agent
that reads AGENTS.md. It is the tool-agnostic distillation of the token-lean
Claude Code plugin — no hooks required.

## Read less

- Locate before reading: search for the symbol, then read only the matching
  region. Never read a whole file when a 60-line window answers the question.
- Never re-read a file already in context unless it changed on disk.
- Use terse command flags: `git status --porcelain -b`, `git log --oneline -15`,
  `git diff --stat` first, `ls -1`, `pytest -q`.
- Pipe long output through filters (`| head -50`, `| grep <pattern>`). Never
  dump raw logs, full test output, or dependency trees.

## Write less

Before writing any code, stop at the first rung that works:

1. Does this need to exist at all? Deleting code can be the fix.
2. Does it already exist in the codebase? Reuse or extend it.
3. Does the standard library cover it? No new dependency.
4. Can it be one line, or a few? No speculative parameters or wrappers.
5. Only then write new code — and make it small.

No dead code "for later", no duplicated logic, no boilerplate comments, no
docstrings that restate the signature.

## Say less

- Answer first; detail only if asked.
- Do not narrate steps or restate the task. Show the result.
- One-sentence completion notes. Never paste back code just written to a file.
- Match answer length to question weight.

## When NOT to economize

- Correctness-critical reads (security review, migrations): read everything.
- The user explicitly asks for detail or teaching.
- Ambiguity where a wrong guess costs a full redo: ask one precise question.
