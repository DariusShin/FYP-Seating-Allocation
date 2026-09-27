"""Parameterized synthetic production fixtures. Counts are allocation units, not people."""

import argparse
import copy
import random
from functools import lru_cache

from seat_solver.prototype.models import read_json, write_json
from seat_solver.production.policy import MINIMUMS, ROOT


# Deterministic, fictitious Chinese names; separate from the allocation RNG so
# changing display names does not alter contribution/activity test scenarios.
@lru_cache(maxsize=16)
def _name_order(seed):
    return random.Random(seed).sample(range(8000), 8000)


def synthetic_chinese_name(index, seed=20260918):
    surnames = "陳林黃張李王吳劉蔡楊許鄭謝郭何周羅梁宋葉"
    first = "志慧思嘉俊美文欣明雅建靜偉淑國佩德雪錦秀"
    last = "華玲恩怡傑萱軒婷豪敏安儀賢雯成芬宇寧瑞琳"
    n = _name_order(seed)[index % 8000]
    return surnames[n % 20] + first[(n // 20) % 20] + last[n // 400]


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


def refresh_synthetic_display_names(store):
    """Replace recognized placeholder display names in private working drafts only.

    This explicit fixture migration preserves custom names, notes, placements,
    registrations and all published snapshots.
    """
    import re

    from seat_solver.production.workspace import WorkspaceStore

    workspaces = WorkspaceStore(store)
    with store.connection() as db:
        events = [row[0] for row in db.execute("SELECT DISTINCT event FROM plans")]
    changed = 0
    for event in events:
        current = workspaces.load(event)
        state = current["state"]
        updated = 0
        for index, p in enumerate(state["participants"]):
            if not re.fullmatch(r"Synthetic participant \d+", p["full_name"]):
                continue
            item = state["items"][p["participant_id"]]
            for occupant, name in enumerate(item["display_names"]):
                if name == p["full_name"] or re.fullmatch(
                    r"Synthetic (?:partner|guest) \d+", name
                ):
                    item["display_names"][occupant] = synthetic_chinese_name(index)
                    updated += 1
        if updated:
            workspaces.action(
                event,
                "synthetic-fixture-update",
                {
                    "command": "workspace_save",
                    "plan_version_id": current["base"]["plan_version_id"],
                    "revision": current["revision"],
                    "state": state,
                },
            )
            changed += updated
    return changed
