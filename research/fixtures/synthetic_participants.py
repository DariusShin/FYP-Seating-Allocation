"""Parameterized synthetic production fixtures. Counts are allocation units, not people.

Shared by production tests and research experiments; the application runtime
never imports this module. Display names come from the deterministic generator
in seat_solver.production.production_data so fixture labels and workspace name
restoration stay consistent.
"""

import argparse
import copy
import random

from seat_solver.jsonio import read_json, write_json
from seat_solver.production.policy import MINIMUMS, RESOURCES
from seat_solver.production.production_data import synthetic_chinese_name


def generate(emperor=56, merit=24, bodhi=16, seed=20260918, accessible=0):
    if (
        any(type(v) is not int or v < 0 for v in (emperor, merit, bodhi, accessible))
        or accessible > emperor + merit + bodhi
    ):
        raise ValueError(
            "Counts must be nonnegative; accessibility count cannot exceed registrations"
        )
    req = read_json(RESOURCES / "data/production_request.json")
    rng = random.Random(seed)
    req["participants"] = []
    tiers = ["EMPEROR"] * emperor + ["MERIT"] * merit + ["BODHI"] * bodhi
    accessible_ids = set(rng.sample(range(len(tiers)), accessible))
    for i, tier in enumerate(tiers):
        req["participants"].append(
            {
                "participant_id": f"P{i + 1:04d}",
                "full_name": synthetic_chinese_name(i, seed),
                "registration_status": "CONFIRMED",
                "contribution_tier": tier,
                "contribution_amount_rm": MINIMUMS[tier]
                + rng.choice([0, 100, 200, 500, 1000]),
                "requires_accessible_seat": i in accessible_ids,
                "participant_category": rng.choice(
                    ["MONASTIC", "COMMITTEE", "VOLUNTEER", "GENERAL_DEVOTEE"]
                ),
                "events_joined_last_2_years": rng.randrange(20),
                "age": rng.randrange(18, 90),
                "adjacent_person_name": None,
            }
        )
    req["solver"]["random_seed"] = seed
    return copy.deepcopy(req)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for k, v in [
        ("emperor", 56),
        ("merit", 24),
        ("bodhi", 16),
        ("seed", 20260918),
        ("accessible", 0),
    ]:
        p.add_argument("--" + k, type=int, default=v)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    write_json(a.output, generate(a.emperor, a.merit, a.bodhi, a.seed, a.accessible))


if __name__ == "__main__":
    main()
