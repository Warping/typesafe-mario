"""Turn logged Mario decisions into Laya fine-tuning rows and run fine-tuning."""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

from .actions import Action
from .policy import build_questions
from .teacher import teacher_answers


def rows_from_logs(paths: Iterable[Path], frames_per_decision: int = 8) -> Iterator[dict[str, Any]]:
    questions = build_questions(tuple(Action), frames_per_decision)
    for path in paths:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            state = json.loads(line)["state"]
            answers = teacher_answers(state)
            yield {
                "state": state,
                "questions": questions,
                "expected": {
                    "next_action": answers["next_action"].value,
                    "jump_needed": answers["jump_needed"],
                    "danger": answers["danger"],
                },
            }


def write_dataset(rows: Iterable[dict[str, Any]], out: Path) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
            count += 1
    return count


def finetune_laya(
    data: Path,
    output_dir: Path,
    *,
    base: str = "english",
    device: str = "cuda",
    epochs: int = 2,
    micro_batch: int = 4,
    grad_accum: int = 8,
    freeze_encoder: bool = False,
    log_every: int = 10,
) -> None:
    from laya.train import TrainConfig, finetune, resolve_checkpoint_dir

    model_dir = resolve_checkpoint_dir(base)
    config = TrainConfig(
        epochs=epochs,
        micro_batch=micro_batch,
        grad_accum=grad_accum,
        freeze_encoder=freeze_encoder,
        gradient_checkpointing=True,
        log_every=log_every,
    )
    print(f"[{datetime.now():%H:%M:%S}] starting fine-tune: base={base} data={data} out={output_dir}", flush=True)
    finetune(str(data), model_dir, str(output_dir), config=config, device=device)
    print(f"[{datetime.now():%H:%M:%S}] fine-tune finished", flush=True)
