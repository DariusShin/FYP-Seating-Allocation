"""Tiny exhaustive oracles and scorer/formulation equivalence gates."""

import copy
import itertools

from research.fixtures.synthetic_participants import generate
from seat_solver.production.policy import TIERS, policy
from seat_solver.production.production_scoring import candidate_cost, eligible
from .common import CONFIGS, KEYS, METHODS, compact_weights, execute, preferences, reference_components


def tiny(emperor=0, merit=2, bodhi=0, coordinates=((1, 9), (1, 10), (1, 11), (1, 12))):
    request = generate(emperor, merit, bodhi, seed=20261019)
    request.pop("attendance", None)
    request["generation_mode"] = "INITIAL"
    layout = request["layout"]
    layout["row_count"] = max(row for row, _ in coordinates)
    layout["seats"] = [s for s in layout["seats"] if s["row_number"] <= layout["row_count"]]
    for seat in layout["seats"]:
        seat["is_blocked"] = (seat["row_number"], seat["physical_position"]) not in coordinates
    request["layout_version_id"] = layout["layout_version_id"] = "benchmark-tiny-oracle-v1"
    return request


def oracle(request):
    """Enumerate physical bundles without production options/model/row-pruning helpers.

    Packing fixes the occupied row-major priority prefix. Direct pairwise checks
    enforce ordering, and Cartesian enumeration covers every assignment to it.
    """
    people = eligible(request)
    cfg, weights = policy(), compact_weights(request)
    demand = sum(2 if p["contribution_tier"] == "EMPEROR" else 1 for p in people)
    available = sorted((s for s in request["layout"]["seats"] if not s["is_blocked"]),
                       key=lambda s: (s["row_number"], s["priority_rank"]))
    if demand > len(available):
        return None
    occupied = available[:demand]
    lookup = {(s["row_number"], s["physical_position"]): s for s in occupied}
    domains = []
    for p in people:
        if p["contribution_tier"] == "EMPEROR":
            domain = [(lookup[row, a], lookup[row, b])
                      for row in range(1, request["layout"]["row_count"] + 1)
                      for a, b in request["layout"]["approved_pairs"] if (row, a) in lookup and (row, b) in lookup]
        else:
            domain = [(s,) for s in occupied]
        domains.append([o for o in domain if not p["requires_accessible_seat"] or all(s["is_accessible"] for s in o)])
    best = None
    width = request["layout"]["seats_per_row"]
    for arrangement in itertools.product(*domains):
        ids = [s["seat_id"] for option in arrangement for s in option]
        if len(set(ids)) != demand:
            continue
        valid = True
        for i, p in enumerate(people):
            for j in range(i + 1, len(people)):
                q = people[j]
                pt, qt = TIERS.index(p["contribution_tier"]), TIERS.index(q["contribution_tier"])
                po = [(s["row_number"] - 1) * width + s["priority_rank"] for s in arrangement[i]]
                qo = [(s["row_number"] - 1) * width + s["priority_rank"] for s in arrangement[j]]
                if (pt < qt and max(po) >= min(qo)) or (pt > qt and max(qo) >= min(po)):
                    valid = False
                if pt == qt and (p["contribution_amount_rm"] - q["contribution_amount_rm"]) * (arrangement[i][0]["row_number"] - arrangement[j][0]["row_number"]) > 0:
                    valid = False
        if valid:
            total = sum(sum(weights[k] * reference_components(request, cfg, p, option)[k] for k in KEYS)
                        for p, option in zip(people, arrangement))
            best = total if best is None else min(best, total)
    return best


def correctness():
    cases = {"singles": tiny(), "mixed_tiers": tiny(1, 1, 1),
             "two_rows": tiny(0, 4, 0, ((1, 9), (1, 10), (2, 9), (2, 10))),
             "two_pairs": tiny(2, 0, 0), "empty": tiny(0, 0, 0),
             "capacity_infeasible": tiny(0, 5, 0)}
    inaccessible = tiny(0, 1, 0)
    inaccessible["participants"][0]["requires_accessible_seat"] = True
    cases["accessibility_infeasible"] = inaccessible
    accessible = tiny(1, 0, 0, ((1, 15), (1, 16)))
    accessible["participants"][0]["requires_accessible_seat"] = True
    cases["accessible_pair"] = accessible
    equal = tiny()
    for p in equal["participants"]:
        p["events_joined_last_2_years"] = 0
        p["contribution_amount_rm"] = 3000
    cases["equal_scores"] = equal
    rows = []
    for name, original in cases.items():
        for config in CONFIGS:
            request = copy.deepcopy(original)
            request["preferences"] = preferences(config)
            expected = oracle(request)
            for method in METHODS:
                result = execute(request, method, 2)
                if method != "greedy":
                    if expected is None:
                        assert result["solver_status"] == "INFEASIBLE", (name, config, method, result)
                    else:
                        assert result["valid"] and result["solver_status"] == "OPTIMAL", (name, config, method, result)
                        assert result["objective"] == expected, (name, config, method, expected, result)
                elif result["valid"]:
                    assert expected is not None and result["objective"] >= expected
                else:
                    assert result["solver_status"] in ("CONSTRUCTION_FAILED", "TIME_LIMIT")
                rows.append({"case": name, "configuration": config, "method": method,
                             "oracle_objective": expected, "solver_status": result["solver_status"],
                             "valid": result["valid"], "objective": result["objective"]})
    # Every legal tiny option is independently rescored, including unchosen options.
    from .common import prepare
    checked = 0
    for request in cases.values():
        problem = prepare(request)
        seats = {s["seat_id"]: s for s in request["layout"]["seats"]}
        for pid, bundles in problem.bundles.items():
            for bundle in bundles:
                option = [seats[s] for s in bundle.ids]
                assert reference_components(request, problem.cfg, problem.people[pid], option) == candidate_cost(request, problem.cfg, problem.people[pid], option)["normalized"]
                checked += 1
    return {"passed": True, "cases": rows, "checked_option_vectors": checked,
            "note": "Separate correctness suite; no records enter benchmark denominators"}
