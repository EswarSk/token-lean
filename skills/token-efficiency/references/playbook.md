# Token Efficiency Playbook

Extended rationale and patterns behind the three pillars. Load only when deeper guidance is needed.

## Where tokens actually go

A session's context is consumed by: system prompt and tool schemas (fixed), CLAUDE.md and memory files (user-controlled), file reads and command output (largest variable cost), and model output (compounds — everything written is re-read on every subsequent turn).

Implication: the highest-leverage habits are avoiding redundant input (Pillar 1) and shrinking output (Pillars 2–3), because output becomes input on every following turn.

A second-order cost: cache misses. Anthropic's prompt cache has a short TTL, and any change near the top of the context invalidates it. Stable instructions (CLAUDE.md, skills) should change rarely; volatile content belongs at the end of the conversation, not the start.

## Read-less patterns

**Locate-then-read.** Grep for the symbol → note line numbers → Read with offset/limit around them. A 2,000-line file read costs ~20k tokens; a 60-line window costs ~600.

**Diff-first review.** For "what changed" questions, `git diff --stat` first, then targeted `git diff -- <file>` only for files that matter.

**Structured probes over dumps.** Ask for the shape before the content: `wc -l`, `head -20`, `python -c "import json;d=json.load(open('f'));print(list(d))"`. Then fetch only the needed slice.

**Subagent isolation.** Repo-wide searches, dependency audits, and log forensics generate thousands of tokens of intermediate noise. Run them in the `scout` subagent; only the answer returns to the main context. Do not use subagents for trivial one-command tasks — the overhead exceeds the savings.

**Compact early.** Compaction quality degrades with context bloat. Compacting at 60-70% capacity produces a far better summary than compacting at 95% when the model is already forgetting.

**Keep CLAUDE.md lean.** Instructions files are re-read every session. Strip anything the model can infer from the code itself; measured cases show 90%+ reduction with no quality loss.

## Write-less patterns

The decision ladder (SKILL.md Pillar 2) in practice:

- Bug report about a helper nobody calls → delete the helper (rung 1).
- "Add retry logic" → the HTTP client already supports `retries=3` (rung 2).
- "Parse this date" → stdlib `datetime.fromisoformat` (rung 3).
- "Filter and dedupe this list" → one comprehension + `dict.fromkeys` (rung 4).

Anti-patterns that inflate output tokens: speculative config options, wrapper classes around single functions, re-exporting modules, verbose docstrings restating signatures, defensive checks for impossible states, scaffolded test boilerplate for untestable glue.

Benchmark context: minimal-code discipline has measured 50-90% fewer generated lines and 20-70% lower cost on real repos, with no loss in correctness — less code is not less safe.

## Say-less patterns

- Lead with the answer or the artifact. Rationale only on request.
- One-sentence completion notes: "Fixed the off-by-one in `paginate()`; tests pass."
- Never paste back code just written to a file.
- Never enumerate steps about to be taken; take them.

## Hook interplay

This plugin's hooks enforce Pillar 1 mechanically:

- **read-guard** denies re-reads of unchanged files (first attempt) with a pointer to use existing context or a targeted Grep. Small files (< 2 KB) are exempt — re-reading them costs less than the friction. A deliberate immediate retry is allowed, so it never hard-blocks. Read state is cleared on compaction, since compacted context no longer contains earlier file reads.
- **bash-guard** denies known-verbose commands once, suggesting the terse equivalent (`git status` → `--porcelain -b`, `git log` → `--oneline -15`, bare `cat` → `head -100`, `grep -r`/`find` → Grep/Glob tools). Retrying the identical command passes through.

Treat a hook denial as a nudge, not an error: adopt the suggested form.

## When NOT to economize

- Correctness-critical reads (security review, migration scripts): read the whole file.
- User explicitly asks for detail, teaching, or exhaustive output.
- Ambiguity where a wrong guess costs a full redo — one clarifying question is cheaper.
