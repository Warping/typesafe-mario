"""Rule-based answers to the three Laya questions, used as fine-tuning labels."""

from __future__ import annotations

import random
import time
from collections.abc import Mapping, Sequence
from typing import Any

from .actions import Action
from .policy import Decision
from .state import MarioSnapshot

DANGER_NONE, DANGER_SOON, DANGER_IMMEDIATE = 0, 1, 2


def _flag(state: Mapping[str, Any], key: str) -> bool:
    for section in state.values():
        if isinstance(section, Mapping) and section.get(key):
            return True
    return False


def teacher_answers(state: Mapping[str, Any]) -> dict[str, Any]:
    jump_now = _flag(state, "jump_must_start_this_decision")
    contact = _flag(state, "contact_within_reaction_horizon")
    enemy = _flag(state, "enemy_ahead")
    obstacle = _flag(state, "obstacle_ahead")
    gap = _flag(state, "gap_ahead")
    crossing = _flag(state, "crossing_known_gap")

    needs_jump = jump_now or contact or obstacle or gap or crossing
    if jump_now or contact:
        danger = DANGER_IMMEDIATE
    elif enemy or obstacle or gap:
        danger = DANGER_SOON
    else:
        danger = DANGER_NONE
    return {
        "next_action": Action.RIGHT_RUN_JUMP if needs_jump else Action.RIGHT_RUN,
        "jump_needed": needs_jump,
        "danger": danger,
    }


class RuleTeacherPolicy:
    """Policy that plays with the rule teacher; a reference for the fine-tuned model.

    With epsilon > 0 it sometimes plays a random allowed action, so the logged states cover
    more situations. The logged labels still come from the rules, not from the random action.
    """

    def __init__(self, epsilon: float = 0.0, seed: int = 0) -> None:
        self._epsilon = epsilon
        self._rng = random.Random(seed)

    def choose(self, snapshot: MarioSnapshot, actions: Sequence[Action]) -> Decision:
        started = time.perf_counter()
        answers = teacher_answers(snapshot.to_state())
        action = answers["next_action"] if answers["next_action"] in actions else actions[0]
        if self._epsilon and self._rng.random() < self._epsilon:
            action = self._rng.choice(list(actions))
        return Decision(
            action=action,
            confidence=1.0,
            probabilities={candidate.value: float(candidate == action) for candidate in actions},
            latency_ms=(time.perf_counter() - started) * 1000,
            jump_needed_probability=float(answers["jump_needed"]),
            danger_score=float(answers["danger"]),
        )
