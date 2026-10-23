# Laya Mario

An experimental controller that lets a local [Laya](https://github.com/NandhaKishorM/laya)
model directly choose NES controller inputs for the original Super Mario Bros.

The model does **not** receive screenshots. The harness translates emulator telemetry
and RAM into compact, object-centric JSON containing Mario's motion, jump trajectory,
upcoming enemies, terrain, measured response delay, recent-control results, and episode
progress. Laya chooses one of the legal controller actions, the emulator advances several
frames, and the loop repeats. The raw local tile grid remains available in debug logs
and the UI, but is not duplicated in the model input.

## Architecture

```text
NES emulator -> telemetry/RAM parser -> structured JSON -> Laya Choice -> controller input
```

The initial action set is intentionally small:

- `noop`
- `right`
- `right_jump`
- `right_run`
- `right_run_jump`
- `jump`
- `left`

## Requirements

- Python 3.13 or newer (the project requirement; Laya itself needs 3.10+)
- A legal local setup for Super Mario Bros.
- Internet access on first run, to download the Laya checkpoint from Hugging Face
  (about 420 MB, cached afterwards). No API key is needed.

This repository contains no Nintendo ROM or other copyrighted game data. You are
responsible for ensuring that your emulator and game files are obtained and used
lawfully.

## Setup

```powershell
uv sync --extra mario --extra dev
```

Inspect the exact JSON and text that will be sent to the model without launching the
game or running the model:

```powershell
.venv\Scripts\typesafe-mario state-demo
```

Run World 1-1 with Laya making a decision every eight emulator steps. The default
display is a single recordable window with the live game and model telemetry:

```powershell
.venv\Scripts\typesafe-mario play --env SuperMarioBros-1-1-v0 --frames-per-decision 8
```

Use `--policy heuristic` to run the offline baseline without loading a model.

The dashboard shows the selected action, full Choice probability distribution,
confidence, Laya latency, jump probability, danger score, reward, and parsed game
state. Press `R` or click **Restart** for a fresh episode; the dashboard remains open
after death or level completion. Press `Esc` or `Q` to quit. Use `--display game` for
only the emulator window or `--display none` for a headless benchmark.

Each decision is written to `artifacts/run-<timestamp>.jsonl`. These records include
latency, action probabilities, confidence, canonical model state, raw debug state, and
game outcome, providing the data for a live overlay or rendered social clip.

## What the parser produces

Laya takes the state as a JSON object, so there is no need to flatten telemetry into prose.
The model-facing object groups observations by meaning:

- `player`: position, velocity, grounded state, jump phase, and power-up
- `trajectory`: airtime, distance since takeoff, and committed gap crossing
- `hazard`: up to three enemies, projected positions, contact timing, and takeoff deadline
- `terrain`: obstacle/gap geometry, observation reliability, and last grounded preview
- `reaction_timing`: action duration and measured observation-to-action delay
- `recent_control`: chosen action, duration, progress gained, and observed outcome
- `episode`: lives, clock, progress, stalls, death, and level completion

For humans, the fuller debug snapshot can still be rendered as compact text:

```text
Goal: Reach the flag in World 1-1 without dying.
Mario: x=172 y=79, moving right, airborne=False, status=small
Progress: 172 (best 172), time=387, lives=2
Nearby enemies: goomba 42px ahead
Local grid (# solid, . empty, E enemy, M Mario):
...........
...........
...........
..M..E.....
###########
```

The structured object is canonical; the text view is only for debugging and UI.

## Laya judgments

Each decision asks three independent questions over the same state, using
`laya-typed-decisions` (1024-token context):

- a `choice` selects the next controller macro;
- a `noul` estimates whether a forward jump is useful now;
- a `score` measures immediate danger for the live visualization.

Exact timing arithmetic stays in code. For example, the parser combines measured
response age, enemy motion, action cadence, and jump-clearance time into a typed
`jump_must_start_this_decision` fact. Laya interprets those facts and still owns the
controller choice—there is no scripted recovery-action override.

The policy lives in [policy.py](src/typesafe_mario/policy.py) as `LayaPolicy`.
`Router.predict` runs locally, so each decision costs a forward pass over the
checkpoint on your machine rather than a network call.

## Development

```powershell
.venv\Scripts\ruff format --check src tests
.venv\Scripts\ruff check src tests
.venv\Scripts\python -m pytest -q
```
