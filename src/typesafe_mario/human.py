"""Keyboard policy for recording human demonstrations on Windows.

Keys: Right/Left arrows move, Z is A (jump), X is B (run). The keys held at each
decision boundary become that decision's action, so human play is logged in the
same format as every other policy.
"""

from __future__ import annotations

import sys
import time
from collections.abc import Callable, Mapping, Sequence

from .actions import Action
from .policy import Decision
from .state import MarioSnapshot

VK_LEFT = 0x25
VK_RIGHT = 0x27
VK_Z = 0x5A
VK_X = 0x58

KEY_NAMES: Mapping[str, int] = {"left": VK_LEFT, "right": VK_RIGHT, "a": VK_Z, "b": VK_X}


def held_action(keys: frozenset[str]) -> Action:
    """Map the set of held logical buttons ('left', 'right', 'a', 'b') to an action."""
    if "right" in keys:
        jump = "a" in keys
        run = "b" in keys
        if jump and run:
            return Action.RIGHT_RUN_JUMP
        if jump:
            return Action.RIGHT_JUMP
        if run:
            return Action.RIGHT_RUN
        return Action.RIGHT
    if "left" in keys:
        return Action.LEFT
    if "a" in keys:
        return Action.JUMP
    return Action.NOOP


def _windows_key_down(vk: int) -> bool:
    import ctypes

    return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)  # type: ignore[attr-defined]


class HumanPolicy:
    """Reads the physical keyboard at each decision. The game window must have focus."""

    def __init__(self, key_down: Callable[[int], bool] | None = None) -> None:
        if key_down is None and sys.platform != "win32":
            raise RuntimeError("The human policy reads keys with Windows GetAsyncKeyState.")
        self._key_down = key_down or _windows_key_down

    def held_keys(self) -> frozenset[str]:
        return frozenset(name for name, vk in KEY_NAMES.items() if self._key_down(vk))

    def choose(self, snapshot: MarioSnapshot, actions: Sequence[Action]) -> Decision:
        started = time.perf_counter()
        action = held_action(self.held_keys())
        if action not in actions:
            action = Action.NOOP
        return Decision(
            action=action,
            confidence=1.0,
            probabilities={candidate.value: float(candidate == action) for candidate in actions},
            latency_ms=(time.perf_counter() - started) * 1000,
            jump_needed_probability=float(
                action in {Action.RIGHT_JUMP, Action.RIGHT_RUN_JUMP, Action.JUMP}
            ),
            danger_score=0.0,
        )
