"""Pure physical-placement scoring. Integer scales are documented in mathematical_model.json."""

from seat_solver.policy import ELIGIBLE, TIERS, mapped_weights


def eligible(request):
    return sorted(
        (p for p in request["participants"] if p["registration_status"] in ELIGIBLE),
        key=lambda p: p["participant_id"],
    )


def options(request, participant):
    layout = request["layout"]
    available = [s for s in layout["seats"] if not s["is_blocked"]]
    if participant["contribution_tier"] == "EMPEROR":
        by = {(s["row_number"], s["physical_position"]): s for s in available}
        pairs = [
            (by[r, a], by[r, b])
            for r in range(1, layout["row_count"] + 1)
            for a, b in layout["approved_pairs"]
            if (r, a) in by and (r, b) in by
        ]
        return [
            pair
            for pair in pairs
            if not participant["requires_accessible_seat"]
            or all(s["is_accessible"] for s in pair)
        ]
    return [
        (s,)
        for s in available
        if not participant["requires_accessible_seat"] or s["is_accessible"]
    ]


def half_up(n, d):
    return (2 * n + d) // (2 * d) if d else 0


def candidate_cost(request, cfg, p, seats):
    peers = [
        q for q in eligible(request) if q["contribution_tier"] == p["contribution_tier"]
    ]
    amounts = [q["contribution_amount_rm"] for q in peers]
    activities = [q["events_joined_last_2_years"] for q in peers]
    c = 1 + half_up(
        99 * (p["contribution_amount_rm"] - min(amounts)),
        max(1, max(amounts) - min(amounts)),
    )
    a = half_up(
        100 * (p["events_joined_last_2_years"] - min(activities)),
        max(1, max(activities) - min(activities)),
    )
    tier_bonus = (
        0
        if p["requires_accessible_seat"]
        else 100 * (2 - TIERS.index(p["contribution_tier"]))
    )
    # Twice the mean rank disadvantage, identical physical scale for singles and pairs.
    disadvantage = 2 * sum(s["priority_rank"] - 1 for s in seats) // len(seats)
    zone = (
        2
        * sum(
            cfg["category_zone_costs"][p["participant_category"]][s["zone"]]
            for s in seats
        )
        // len(seats)
    )
    raw = {
        "contribution_seat": (c + tier_bonus) * disadvantage,
        "activeness": a * disadvantage,
        "category_zone": zone,
    }
    maxima = {
        "contribution_seat": 300 * 2 * (request["layout"]["seats_per_row"] - 1),
        "activeness": 100 * 2 * (request["layout"]["seats_per_row"] - 1),
        "category_zone": 2
        * max(
            v for costs in cfg["category_zone_costs"].values() for v in costs.values()
        ),
    }
    norm = {k: half_up(v * 100, max(1, maxima[k])) for k, v in raw.items()}
    weights = mapped_weights(
        request["preferences"], request["preference_profile_version"]
    )
    weighted = {k: weights[k] * v for k, v in norm.items()}
    return {
        "unweighted": raw,
        "normalized": norm,
        "weighted": {**weighted, "total": sum(weighted.values())},
    }


def baseline_maps(baseline):
    if not baseline:
        return {}, {}
    return (
        {a["participant_id"]: tuple(a["seat_ids"]) for a in baseline["assignments"]},
        {p["participant_id"]: p for p in baseline["source_request"]["participants"]},
    )


def changed_ids(request, baseline):
    _, old = baseline_maps(baseline)
    # Ignore names, but include all attributes with allocation or eligibility consequences.
    fields = (
        "registration_status",
        "contribution_tier",
        "contribution_amount_rm",
        "requires_accessible_seat",
        "participant_category",
        "events_joined_last_2_years",
        "replacement_for_participant_id",
    )
    new = {p["participant_id"]: p for p in request["participants"]}
    changes = {
        pid
        for pid in old.keys() | new.keys()
        if pid not in old
        or pid not in new
        or any(old[pid].get(k) != new[pid].get(k) for k in fields)
    }
    if baseline:
        current = {s["seat_id"]: s for s in request["layout"]["seats"]}
        for assignment in baseline["assignments"]:
            p = new.get(assignment["participant_id"])
            for sid in assignment["seat_ids"]:
                s = current.get(sid)
                if (
                    not s
                    or s["is_blocked"]
                    or (p and p["requires_accessible_seat"] and not s["is_accessible"])
                ):
                    changes.add(assignment["participant_id"])
    return changes


def movement(p, seats, baseline, request):
    previous, _ = baseline_maps(baseline)
    ids = previous.get(p["participant_id"])
    if ids is None:
        return 0, 0
    moved = int(set(ids) != {s["seat_id"] for s in seats})
    old = {s["seat_id"]: s for s in baseline["source_request"]["layout"]["seats"]}
    oldseats = [old[sid] for sid in ids]

    # Doubled centroid Manhattan distance: integer for one-seat and two-seat units.
    def centre(items, key):
        return 2 * sum(s[key] for s in items) // len(items)

    distance = abs(centre(oldseats, "row_number") - centre(seats, "row_number")) + abs(
        centre(oldseats, "physical_position") - centre(seats, "physical_position")
    )
    return moved, distance


def packing_pairs(layout):
    available = [s for s in layout["seats"] if not s["is_blocked"]]
    comparisons = []
    for r in range(1, layout["row_count"] + 1):
        for side, reverse in [("LEFT", True), ("RIGHT", False)]:
            ordered = sorted(
                (s for s in available if s["row_number"] == r and s["side"] == side),
                key=lambda s: s["physical_position"],
                reverse=reverse,
            )
            # All inner/outer inversions (not merely adjacent gaps).
            comparisons.extend(
                (a["seat_id"], b["seat_id"])
                for i, a in enumerate(ordered)
                for b in ordered[i + 1 :]
            )
    return comparisons


def quality(request, cfg, placements, baseline=None):
    lookup = {s["seat_id"]: s for s in request["layout"]["seats"]}
    ps = eligible(request)
    changes = changed_ids(request, baseline)
    penalties = {
        p["participant_id"]: candidate_cost(
            request, cfg, p, [lookup[s] for s in placements[p["participant_id"]]]
        )
        for p in ps
    }
    raw = {
        k: sum(c["unweighted"][k] for c in penalties.values())
        for k in mapped_weights(request["preferences"])
    }
    normalized = {k: sum(c["normalized"][k] for c in penalties.values()) for k in raw}
    weighted = {k: sum(c["weighted"][k] for c in penalties.values()) for k in raw}
    moved = unaffected = distance = physical = 0
    for p in ps:
        m, d = movement(
            p, [lookup[s] for s in placements[p["participant_id"]]], baseline, request
        )
        moved += m
        unaffected += m * (p["participant_id"] not in changes)
        distance += d
        physical += m * len(placements[p["participant_id"]])
    occupied = {s for ids in placements.values() for s in ids}
    local = sum(
        a not in occupied and b in occupied for a, b in packing_pairs(request["layout"])
    )
    return {
        "penalties": penalties,
        "unweighted": raw,
        "normalized": normalized,
        "weighted": {**weighted, "total": sum(weighted.values())},
        "movement": {
            "moved_units": moved,
            "unaffected_moved_units": unaffected,
            "moved_physical_seats": physical,
            "distance_doubled": distance,
        },
        "local_packing": local,
    }
