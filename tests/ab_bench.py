#!/usr/bin/env python3
"""A/B benchmark: same task with token-lean enabled vs disabled.

Usage:
    python3 tests/ab_bench.py "your coding task prompt" [runs_per_side]

Runs the prompt in fresh headless sessions N times per condition (default 3),
toggling the plugin between conditions, and reports median cost and tokens.
Note: consumes API/plan usage — keep the task small but realistic.
"""
import json
import statistics
import subprocess
import sys

PLUGIN = "token-lean@token-lean"


def run_once(prompt):
    p = subprocess.run(
        ["claude", "-p", "--output-format", "json"],
        input=prompt, capture_output=True, text=True, timeout=1200,
    )
    d = json.loads(p.stdout)
    u = d.get("usage") or {}
    return {
        "cost": d.get("total_cost_usd") or 0.0,
        "in": u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0)
              + u.get("cache_creation_input_tokens", 0),
        "out": u.get("output_tokens", 0),
        "turns": d.get("num_turns", 0),
    }


def toggle(enabled):
    subprocess.run(["claude", "plugin", "enable" if enabled else "disable",
                    PLUGIN], capture_output=True)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    prompt = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    results = {}
    for label, enabled in [("plugin OFF", False), ("plugin ON", True)]:
        toggle(enabled)
        runs = []
        for i in range(n):
            r = run_once(prompt)
            print(f"{label} run {i+1}: ${r['cost']:.4f}  "
                  f"in={r['in']}  out={r['out']}  turns={r['turns']}")
            runs.append(r)
        results[label] = runs
    toggle(True)  # leave enabled

    print("\n=== medians ===")
    med = {}
    for label, runs in results.items():
        med[label] = {k: statistics.median(r[k] for r in runs)
                      for k in ("cost", "in", "out")}
        m = med[label]
        print(f"{label}: ${m['cost']:.4f}  in={m['in']:.0f}  out={m['out']:.0f}")
    off, on = med["plugin OFF"], med["plugin ON"]
    if off["cost"]:
        print(f"cost delta: {100 * (off['cost'] - on['cost']) / off['cost']:+.1f}% saved")


if __name__ == "__main__":
    main()
