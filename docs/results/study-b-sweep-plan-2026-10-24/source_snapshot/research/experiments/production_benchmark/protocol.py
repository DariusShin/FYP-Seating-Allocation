"""Fixed Study B design, immutable source inputs and semantic identities."""

from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import random
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
STUDY = "production-solver-study-b-v3"
SOURCE = ROOT / "docs/results/solver-selection-v4-21-events-135m-windows-main-2026-10-20-attempt3"
BACKENDS = ("cp_sat", "scip")
THREADS = 8
SEARCH_SEED = 20260918
ORDER_SEED = 20261023
RUNNER_SECONDS = 7200
SWEEP_RUNNER_SECONDS = 9000
PREFLIGHT_SECONDS = 300
PILOT_SECONDS = 900
REPORT_SECONDS = 300
PRIMARY = (
    ("typical-mixed", "current"), ("high-mixed", "current"),
    ("near-mixed", "current"), ("full-mixed", "current"),
    ("heavy-mixed", "current"), ("full-conflict", "reversed"),
    ("full-tied", "disabled"), ("full-accessible", "two"),
)
SWEEP = tuple(PRIMARY[i] for i in (0, 4, 6, 7))
WORKER_LEVELS = (1, 2, 4, 8)
KEYS = ("contribution_seat", "activeness", "category_zone")
CONFIGS = {"current": KEYS, "reversed": tuple(reversed(KEYS)),
           "two": (KEYS[0], KEYS[2]), "disabled": ()}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path, value):
    """Durably replace one JSON artifact; tolerate brief Windows sharing locks."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # A unique temporary name avoids concurrent writes sharing one .json.tmp.
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", delete=False,
                                     dir=path.parent, prefix=f".{path.name}.", suffix=".tmp") as stream:
        temporary = Path(stream.name)
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    for attempt in range(12):
        try:
            os.replace(temporary, path)
            return
        except PermissionError as exc:
            if os.name != "nt" or getattr(exc, "winerror", None) not in (5, 32, 33) or attempt == 11:
                raise
            time.sleep(min(0.05 * (2 ** attempt), 0.5))


def preferences(name):
    active = CONFIGS[name]
    return [{"key": k, "enabled": True} for k in active] + [
        {"key": k, "enabled": False} for k in KEYS if k not in active]


def normalize(request):
    """Array order is incidental except ranked preferences, which retain order."""
    result = copy.deepcopy(request)
    result["participants"].sort(key=lambda p: p["participant_id"])
    layout = result["layout"]
    layout["seats"].sort(key=lambda s: s["seat_id"])
    layout["approved_pairs"].sort(key=tuple)
    layout["accessible_positions"].sort()
    return result


def semantic_hash(request):
    result = normalize(request)
    # These govern execution/provenance, not the feasible set or objective.
    result.pop("solver", None)
    result.pop("generation_mode", None)
    return digest(result)


def physical_map(assignments):
    if isinstance(assignments, dict):
        assignments = [{"participant_id": pid, "seat_ids": seats} for pid, seats in assignments.items()]
    ids = [a["participant_id"] for a in assignments]
    if len(set(ids)) != len(ids):
        raise ValueError("Repeated registration in physical map")
    return [{"participant_id": a["participant_id"], "seat_ids": sorted(a["seat_ids"])}
            for a in sorted(assignments, key=lambda a: a["participant_id"])]


def map_hash(assignments):
    return digest(physical_map(assignments))


def job(batch, event, config, backend, budget, repetition=1, permutation=False, workers=THREADS):
    identity = f"{batch}__{event}__{config}__{backend}__w{workers}__r{repetition}"
    return dict(id=identity, batch=batch, event=event, configuration=config, backend=backend,
                budget_seconds=budget, repetition=repetition, permutation=permutation,
                workers=workers, search_seed=SEARCH_SEED)


def schedule():
    result = []
    for batch, budget in (("diagnostic_5", 5), ("diagnostic_30", 30), ("primary", 60)):
        for i, (event, config) in enumerate(PRIMARY):
            for repeat in (1, 2, 3):
                order = BACKENDS if (i + repeat) % 2 else tuple(reversed(BACKENDS))
                result.extend(job(batch, event, config, b, budget, repeat, repeat == 3) for b in order)
    return result


def pilot_schedule():
    return [job("pilot", event, config, backend, budget)
            for event, config, budget in (("full-tied", "disabled", 5), ("heavy-mixed", "current", 60))
            for backend in BACKENDS]


def sweep_schedule():
    result = []
    for i, (event, config) in enumerate(SWEEP):
        for workers in WORKER_LEVELS:
            for repeat in (1, 2, 3):
                order = BACKENDS if (i + workers + repeat) % 2 else tuple(reversed(BACKENDS))
                result.extend(job("sweep", event, config, b, 60, repeat, repeat == 3, workers=workers)
                              for b in order)
    return result


def sweep_pilot_schedule():
    return [job("pilot", "heavy-mixed", "current", b, 60, workers=w)
            for w in WORKER_LEVELS for b in BACKENDS]


def request_for(raw, trial):
    result = copy.deepcopy(raw)
    result["preferences"] = preferences(trial["configuration"])
    result["generation_mode"] = "INITIAL"
    result["solver"].update(max_time_seconds=trial["budget_seconds"], num_search_workers=trial["workers"],
                            random_seed=SEARCH_SEED, require_optimal=False, canonicalize=False)
    if trial["permutation"]:
        rng = random.Random(ORDER_SEED)
        rng.shuffle(result["participants"])
        rng.shuffle(result["layout"]["seats"])
        rng.shuffle(result["layout"]["approved_pairs"])
    return result


def frozen_inputs(out):
    """Read original input evidence, never regenerate it or import old observations."""
    manifest = read(SOURCE / "manifest.json")
    result = {}
    for event, config in PRIMARY:
        source = SOURCE / "inputs" / f"{event}.json"
        raw = read(source)
        expected = manifest["events"][event]["input_sha256"]
        if digest(raw) != expected:
            raise ValueError(f"Study A source input changed: {event}")
        witness = read(SOURCE / "witnesses" / f"{event}.json")
        if digest(witness) != manifest["events"][event]["witness_sha256"]:
            raise ValueError(f"Study A witness changed: {event}")
        save(Path(out) / "inputs" / f"{event}.json", raw)
        save(Path(out) / "witnesses" / f"{event}.json", witness)
        result[event] = dict(configuration=config, source=str(source.relative_to(ROOT)),
                             input_sha256=expected, witness_sha256=digest(witness),
                             registrations=manifest["events"][event]["registrations"],
                             physical_seats=manifest["events"][event]["physical_seats"])
    return result
