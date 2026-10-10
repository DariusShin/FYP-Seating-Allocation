"""Application-side synthetic display-name handling for recorded fixture states.

The synthetic registration generator itself lives in
research/fixtures/synthetic_participants.py; only the deterministic name
primitives and workspace name restoration remain in the application package.
"""

import random
from functools import lru_cache


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


def restore_synthetic_display_names(state):
    """Resolve legacy fixture labels using the original deterministic Chinese names.

    Match the fixture number, not array order or an arbitrary registration ID.
    Staff-entered names and real registration records are left untouched.
    """
    import re

    changed = 0
    for participant in state["participants"]:
        match = re.fullmatch(r"Synthetic participant ([1-9]\d*)", participant["full_name"])
        if not match:
            continue
        replacement = synthetic_chinese_name(int(match[1]) - 1)
        item = state["items"][participant["participant_id"]]
        for index, name in enumerate(item["display_names"]):
            if name == participant["full_name"] or re.fullmatch(r"Synthetic (?:partner|guest) \d+", name):
                item["display_names"][index] = replacement
                changed += 1
    return changed


def refresh_synthetic_display_names(store):
    """Replace recognized placeholder display names in private working drafts only.

    This explicit fixture migration preserves custom names, notes, placements,
    registrations and all published snapshots.
    """
    from seat_solver.production.workspace import WorkspaceStore

    workspaces = WorkspaceStore(store)
    with store.connection() as db:
        events = [row[0] for row in db.execute("SELECT DISTINCT event FROM plans")]
    changed = 0
    for event in events:
        current = workspaces.load(event)
        state = current["state"]
        updated = restore_synthetic_display_names(state)
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
