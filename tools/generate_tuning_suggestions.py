#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def suggest(rule):
    alerts = rule.get("alerts_30d", 0)
    fp_rate = rule.get("fp_rate", 0)
    avg_ms = rule.get("avg_query_ms", 0)
    threshold = rule.get("threshold")

    recs = []
    if alerts > 500 and fp_rate > 0.4:
        if threshold is not None:
            recs.append((f"increase threshold from {threshold} -> {threshold + 5}", f"{alerts} alerts / 30d, FP rate {fp_rate:.0%}"))
        else:
            recs.append(("increase threshold", f"{alerts} alerts / 30d, FP rate {fp_rate:.0%}"))
    if alerts == 0:
        recs.append(("review rule logic", "0 alerts in 30d"))
    if avg_ms > 2000:
        recs.append(("optimize query", f"average query latency {avg_ms} ms"))
    return recs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    rules = json.loads(Path(args.input).read_text(encoding="utf-8-sig"))
    lines = ["# Tuning Suggestions", ""]

    for rule in rules:
        recs = suggest(rule)
        if not recs:
            continue
        lines.append(f"## {rule['rule_id']}")
        for action, reason in recs:
            lines.append(f"- suggestion: {action}")
            lines.append(f"- reason: {reason}")
        lines.append("")

    Path(args.output).write_text("\n".join(lines).strip() + "\n", encoding="utf-8-sig")


if __name__ == "__main__":
    main()

