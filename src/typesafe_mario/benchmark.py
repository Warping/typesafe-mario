from __future__ import annotations

import json
import statistics
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any


def _percentile(values: Sequence[float], fraction: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, round(fraction * (len(ordered) - 1)))
    return ordered[index]


def summarize_run(path: Path) -> dict[str, Any]:
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    if not records:
        raise ValueError(f"{path} contains no decision records")

    latencies = [float(record["latency_ms"]) for record in records]
    cleared = any(record["state"]["episode"]["stage_clear"] for record in records)
    last = records[-1]
    if cleared:
        ended = "stage_clear"
    elif last["terminated"]:
        ended = "death"
    elif last["truncated"]:
        ended = "truncated"
    else:
        ended = "max_decisions"

    jump_probs = [
        float(record["jump_needed_probability"])
        for record in records
        if record["jump_needed_probability"] is not None
    ]
    danger = [
        float(record["danger_score"]) for record in records if record["danger_score"] is not None
    ]
    return {
        "file": str(path),
        "decisions": len(records),
        "ended": ended,
        "best_progress_px": max(int(record["state"]["episode"]["progress"]) for record in records),
        "total_reward": round(sum(float(record["reward"]) for record in records), 2),
        "latency_mean_ms": round(statistics.fmean(latencies), 1),
        "latency_p50_ms": round(_percentile(latencies, 0.5), 1),
        "latency_p95_ms": round(_percentile(latencies, 0.95), 1),
        "mean_jump_needed_p": round(statistics.fmean(jump_probs), 3) if jump_probs else None,
        "mean_danger_score": round(statistics.fmean(danger), 3) if danger else None,
        "actions": dict(Counter(record["action"] for record in records).most_common()),
    }


def format_summary(summary: dict[str, Any]) -> str:
    lines = [f"== {summary['file']}"]
    for key, value in summary.items():
        if key in {"file", "actions"}:
            continue
        lines.append(f"  {key}: {value}")
    lines.append("  actions:")
    total = summary["decisions"]
    for action, count in summary["actions"].items():
        lines.append(f"    {action:<16} {count:>5}  ({count / total:.0%})")
    return "\n".join(lines)
