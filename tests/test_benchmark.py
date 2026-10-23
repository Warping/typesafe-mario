from __future__ import annotations

import json
from pathlib import Path

from typesafe_mario.benchmark import summarize_run


def _record(progress: int, action: str, *, terminated: bool = False, clear: bool = False) -> dict:
    return {
        "state": {"episode": {"progress": progress, "stage_clear": clear}},
        "action": action,
        "reward": 1.0,
        "latency_ms": 100.0 + progress,
        "jump_needed_probability": 0.5,
        "danger_score": 1.0,
        "terminated": terminated,
        "truncated": False,
    }


def test_summarize_run_reports_progress_actions_and_death(tmp_path: Path) -> None:
    log = tmp_path / "run.jsonl"
    records = [
        _record(10, "right_run"),
        _record(40, "right_run_jump"),
        _record(25, "right_run", terminated=True),
    ]
    log.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")

    summary = summarize_run(log)

    assert summary["decisions"] == 3
    assert summary["ended"] == "death"
    assert summary["best_progress_px"] == 40
    assert summary["actions"] == {"right_run": 2, "right_run_jump": 1}
    assert summary["total_reward"] == 3.0
    assert summary["mean_danger_score"] == 1.0


def test_summarize_run_detects_stage_clear(tmp_path: Path) -> None:
    log = tmp_path / "run.jsonl"
    records = [_record(10, "right_run"), _record(3000, "right_run", terminated=True, clear=True)]
    log.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")

    assert summarize_run(log)["ended"] == "stage_clear"
