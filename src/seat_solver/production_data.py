"""Parameterized synthetic production fixtures. Counts are allocation units, not people."""

import argparse
import copy
import random

from seat_solver.models import read_json, write_json
from seat_solver.policy import MINIMUMS, ROOT


# Deterministic, fictitious Chinese names; separate from the allocation RNG so
# changing display names does not alter contribution/activity test scenarios.
def synthetic_chinese_name(index, seed=20260918):
    surnames = "陈林黄张李王吴刘蔡杨许郑谢郭何周罗梁宋叶"
    first = "志慧思嘉俊美文欣明雅建静伟淑国佩德雪锦秀"
    last = "华玲恩怡杰萱轩婷豪敏安仪贤雯成芬宇宁瑞琳"
    n = (index + seed) % (len(surnames) * len(first) * len(last))
    return (
        surnames[n % len(surnames)]
        + first[(n // len(surnames)) % len(first)]
        + last[n // (len(surnames) * len(first))]
    )


def generate(emperor=56, merit=24, bodhi=16, seed=20260918, accessible=0):
    if (
        any(type(v) is not int or v < 0 for v in (emperor, merit, bodhi, accessible))
        or accessible > emperor + merit + bodhi
    ):
        raise ValueError(
            "Counts must be nonnegative; accessibility count cannot exceed registrations"
        )
    req = read_json(ROOT / "data/production_request.json")
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
                "replacement_for_participant_id": None,
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
