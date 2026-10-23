from typesafe_mario.actions import Action
from typesafe_mario.human import held_action


def test_held_keys_map_to_nes_actions() -> None:
    assert held_action(frozenset()) is Action.NOOP
    assert held_action(frozenset({"right"})) is Action.RIGHT
    assert held_action(frozenset({"right", "b"})) is Action.RIGHT_RUN
    assert held_action(frozenset({"right", "a"})) is Action.RIGHT_JUMP
    assert held_action(frozenset({"right", "a", "b"})) is Action.RIGHT_RUN_JUMP
    assert held_action(frozenset({"a"})) is Action.JUMP
    assert held_action(frozenset({"left"})) is Action.LEFT
