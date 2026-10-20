"""Frozen synthetic scenarios and constructive, independently audited witnesses."""

import copy
import random

from research.fixtures.synthetic_participants import generate
from seat_solver.production.policy import MINIMUMS, TIERS, validate_request
from seat_solver.production.production_validator import validate_placements
from .common import CONFIGS, HEAVY_SEED, INPUT_SEED, METHODS, ORDER_SEED, PILOT_SEED, digest, preferences

SIZES = {"small": (8, 8, 8), "typical": (56, 24, 16),
         "high": (62, 31, 24), "near": (73, 37, 29),
         "full": (80, 40, 32), "heavy": (99, 19, 13)}
PATTERNS = ("mixed", "conflict", "tied")
FAMILY_SIZES = ("small", "typical", "high", "near", "full")
LARGE_EVENTS = ("high-mixed", "near-mixed", "full-mixed", "heavy-mixed")
# Certified input digests from the retained 18 October main evidence bundle.
# The expanded protocol may add events but must not silently change these inputs.
RETAINED_INPUT_SHA256 = {
    "small-mixed": "d15a072f0b2b1bee4b8f79bd049ced6304cb8fa19895790285620e834b50f88a",
    "small-conflict": "4e6188a9331894a155511fd57ac3c88588393b638b6884f1028895efa10859b1",
    "small-tied": "b0a830a78351f272592311600d741927ab8b8cafa545131eb212f1c216b0350f",
    "typical-mixed": "0a6981240781112b3ad9fa257df1a56f6540b4613f3844a7341cfb5ad4265b8f",
    "typical-conflict": "bdf1b8e4d078987083dc0bdf600a30cce4ea987f1abd78d7d2a66c6d42289cee",
    "typical-tied": "27c3598140b6fc28962ff80d6dfa4ca263fcf5e9a8c147d53bd527d98c06111b",
    "full-mixed": "5f9fa8803246ad9a0457cdcc51a0f7eeb3407b03e11c7949c71b30049cb368dd",
    "full-conflict": "c0a0aa65665879c541d7b047c981e7d45f0a449f0e4468f4a2de2a32d0c1d715",
    "full-tied": "89c508f5ad4d4c88cf6aa31904e2c528a5686aa5ef0dc4e9e8f1445c29e3d898",
    "heavy-mixed": "29506f1bc179d665bdc4c30ee6ef52a66d30d61eff1a86d0f42974b3c099f949",
    "small-accessible": "6cf220b2c006cbf8534d4a26f47d9c0bf5d6aa96737a0d05b078f90e65e5ab58",
    "typical-accessible": "a454bf2eb7db64d937ab05f46de7c17e792b80f052bbaccea88822e1400dbf2c",
    "full-accessible": "da0e8282cfeca94445ba6867fbdaa0fce757cf109f3b6ddccdd77d424ad4e0cb",
}


def fixture(size, pattern, seed):
    request = generate(*SIZES[size], seed=seed, accessible=0)
    request.pop("attendance", None)
    request["generation_mode"] = "INITIAL"
    request["preferences"] = preferences("current")
    for p in request["participants"]:
        p["full_name"] = "Synthetic " + p["participant_id"]
        if pattern == "conflict":
            extra = p["contribution_amount_rm"] - MINIMUMS[p["contribution_tier"]]
            p["events_joined_last_2_years"] = 20 - extra // 50
        elif pattern == "tied":
            p["contribution_amount_rm"] = MINIMUMS[p["contribution_tier"]]
    return validate_request(request)


def witness(request):
    """Construct tier/contribution ordered prefixes; never consult an optimizer."""
    available = sorted((s for s in request["layout"]["seats"] if not s["is_blocked"]),
                       key=lambda s: (s["row_number"], s["priority_rank"]))
    people = sorted(request["participants"], key=lambda p: (TIERS.index(p["contribution_tier"]),
                                                            -p["contribution_amount_rm"], p["participant_id"]))
    placements, offset = [], 0
    for p in people:
        count = 2 if p["contribution_tier"] == "EMPEROR" else 1
        placements.append({"participant_id": p["participant_id"],
                           "seat_ids": [s["seat_id"] for s in available[offset:offset + count]]})
        offset += count
    audit = validate_placements(request, placements)
    if not audit["passed"]:
        raise ValueError(f"Constructive witness failed: {audit}")
    return {"construction": "tier/contribution ordered physical-seat prefix; no solver", "placements": placements,
            "validation": audit}


def inventory(pilot=False):
    events = {}
    sizes = FAMILY_SIZES
    for size in sizes:
        for pattern in (("mixed",) if pilot else PATTERNS):
            name = f"{size}-{pattern}"
            request = fixture(size, pattern, PILOT_SEED if pilot else INPUT_SEED)
            events[name] = {"request": request, "seed": PILOT_SEED if pilot else INPUT_SEED,
                            "size": size, "pattern": pattern, "accessibility_derivative": False,
                            "witness": witness(request)}
    request = fixture("heavy", "mixed", PILOT_SEED if pilot else HEAVY_SEED)
    events["heavy-mixed"] = {"request": request, "seed": PILOT_SEED if pilot else HEAVY_SEED,
                             "size": "heavy", "pattern": "mixed", "accessibility_derivative": False,
                             "witness": witness(request)}
    if not pilot:
        for size in sizes:
            base = events[f"{size}-mixed"]
            derivative = copy.deepcopy(base)
            request = derivative["request"]
            seats = {s["seat_id"]: s for s in request["layout"]["seats"]}
            accessible = sorted(a["participant_id"] for a in base["witness"]["placements"]
                                if all(seats[s]["is_accessible"] for s in a["seat_ids"]))
            selected = set(accessible[:max(1, len(request["participants"]) // 10)])
            if not selected:
                raise ValueError("Accessibility derivative has no witness-supported candidate")
            for p in request["participants"]:
                p["requires_accessible_seat"] = p["participant_id"] in selected
            derivative.update(accessibility_derivative=True, base_event=f"{size}-mixed",
                              accessible_ids=sorted(selected))
            derivative["witness"]["validation"] = validate_placements(request, derivative["witness"]["placements"])
            if not derivative["witness"]["validation"]["passed"]:
                raise ValueError("Accessibility witness invalid")
            events[f"{size}-accessible"] = derivative
    for name, event in events.items():
        event["request"]["event_id"] = f"BENCH-{'PILOT-' if pilot else ''}{name}"
        if not pilot and name in RETAINED_INPUT_SHA256 and digest(event["request"]) != RETAINED_INPUT_SHA256[name]:
            raise ValueError(f"Retained 18 October input changed: {name}")
    return events


def schedule():
    rng = random.Random(ORDER_SEED)
    def jobs(batch, events, configs, budgets, methods):
        result = [{"id": f"{batch}__{event}__{config}__{method}__{seconds}s", "batch": batch,
                   "event": event, "configuration": config, "method": method, "budget_seconds": seconds}
                  for event in events for config in configs for seconds in budgets for method in methods]
        rng.shuffle(result)
        return result
    names = [f"{size}-{pattern}" for size in FAMILY_SIZES for pattern in PATTERNS]
    names += ["heavy-mixed"] + [f"{size}-accessible" for size in FAMILY_SIZES]
    return (jobs("primary", names, CONFIGS, (5,), METHODS)
            + jobs("budget_sensitivity", LARGE_EVENTS, ("current", "reversed", "two"), (30, 60), METHODS)
            + jobs("prototype", LARGE_EVENTS, ("current",), (60,), ("cp_sat",)))


def pilot_schedule():
    result = [{"id": f"pilot__{size}__{method}__5s", "batch": "pilot", "event": f"{size}-mixed",
               "configuration": "current", "method": method, "budget_seconds": 5}
              for size in SIZES for method in METHODS]
    result += [{"id": f"pilot__heavy__{method}__{seconds}s", "batch": "pilot", "event": "heavy-mixed",
                "configuration": "current", "method": method, "budget_seconds": seconds}
               for seconds in (30, 60) for method in METHODS]
    result += [{"id": f"pilot__prototype__{event}__60s", "batch": "prototype", "event": event,
                "configuration": "current", "method": "cp_sat", "budget_seconds": 60}
               for event in LARGE_EVENTS]
    return result
