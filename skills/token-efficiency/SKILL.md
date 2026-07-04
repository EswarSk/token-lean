---
name: token-efficiency
description: >
  This skill should be used when the user asks to "save tokens", "reduce cost",
  "be token efficient", "token diet", "optimize context", "keep it lean",
  "minimize tokens", or when starting long sessions on large codebases where
  context and cost efficiency matter.
metadata:
  version: "0.2.0"
---

# Token Efficiency

Operate in maximum token efficiency mode. Every token read, written, or spoken must earn its place. Three pillars, applied in this order: read less, write less, say less.

## Pillar 1: Read Less (context hygiene)

- Never read a whole file when a targeted read works. Use Grep to locate, then Read with offset/limit on the matching region.
- Never re-read a file already in context unless it changed. Trust what was read.
- Prefer Glob/Grep over `find`, `grep -r`, or exploratory `ls` chains.
- Use terse command flags by default: `git status --porcelain -b`, `git log --oneline -15`, `git diff --stat` (then targeted diffs), `ls -1`, `pytest -q`.
- Pipe potentially long output through filters: `| head -50`, `| grep <pattern>`, `| tail -20`. Never dump raw logs, full test output, or dependency trees into context.
- For broad exploration ("where is X handled?"), delegate to the `scout` subagent so search noise stays out of the main context; only the conclusion returns.
- When context grows stale or bloated, recommend compacting early — before quality degrades, not after.

## Pillar 2: Write Less (minimal-code decision ladder)

Before writing any code, climb this ladder and stop at the first rung that works:

1. **Does this need to exist at all?** Question the requirement. Sometimes deleting code or config is the fix.
2. **Does it already exist in the codebase?** Search first. Reuse or extend the existing function/pattern.
3. **Does the standard library or a native platform feature cover it?** No new dependency, no new abstraction.
4. **Can it be one line, or a few?** Write the least code that solves the stated problem — no speculative parameters, no "flexibility" nobody asked for, no wrapper classes around single functions.
5. Only then write new code — and make it small.

Corollaries: no dead code "for later", no duplicated logic, no boilerplate comments, no restating types in docstrings. Fewer lines means fewer output tokens now and less context to re-read later.

## Pillar 3: Say Less (terse output)

- No preamble, no recap, no "Great question", no restating the task.
- Answer first. Detail only if asked.
- Do not narrate tool calls or explain each step. Show the result.
- No summaries of what was just done when the diff/file speaks for itself — one sentence max.
- Match answer length to question weight: one-line question, one-line answer.

## Escalation and routing

- Route grunt work (log scans, file summaries, repo-wide searches) to the `scout` subagent — it runs on a cheaper model and returns only conclusions.
- Reserve the most capable model for architecture and hard multi-file debugging.
- Vague tasks burn tokens exploring. If the task is ambiguous enough to force a repo-wide hunt, ask one precise clarifying question instead — a question costs less than a wrong exploration.

For rationale, measured savings, and extended patterns, read `references/playbook.md`.
