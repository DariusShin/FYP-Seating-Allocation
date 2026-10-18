"""Frozen synthetic scenarios and constructive, independently audited witnesses."""

import copy
import random

from research.fixtures.synthetic_participants import generate
from seat_solver.production.policy import MINIMUMS, TIERS, validate_request
from seat_solver.production.production_validator import validate_placements
from .common import CONFIGS, HEAVY_SEED, INPUT_SEED, METHODS, ORDER_SEED, PILOT_SEED, preferences

SIZES = {"small": (8, 8, 8), "typical": (56, 24, 16), "full": (80, 40, 32), "heavy": (99, 19, 13)}
PATTERNS = ("mixed", "conflict", "tied")
LARGE_EVENTS = ("full-mixed", "full-conflict", "full-tied", "heavy-mixed")


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
    sizes = ("small", "typical", "full")
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
    return events


def schedule():
    rng = random.Random(ORDER_SEED)
    def jobs(batch, events, configs, budgets, methods):
        result = [{"id": f"{batch}__{event}__{config}__{method}__{seconds}s", "batch": batch,
                   "event": event, "configuration": config, "method": method, "budget_seconds": seconds}
                  for event in events for config in configs for seconds in budgets for method in methods]
        rng.shuffle(result)
        return result
    names = [f"{size}-{pattern}" for size in ("small", "typical", "full") for pattern in PATTERNS]
    names += ["heavy-mixed"] + [f"{size}-accessible" for size in ("small", "typical", "full")]
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
    result.append({"id": "pilot__prototype__60s", "batch": "prototype", "event": "heavy-mixed",
                   "configuration": "current", "method": "cp_sat", "budget_seconds": 60})
    return result
