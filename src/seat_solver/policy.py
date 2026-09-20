"""Versioned production policy, strict request contract and ranked preferences."""

from __future__ import annotations

import copy
from pathlib import Path

import jsonschema

from seat_solver.models import read_json

ROOT = Path(__file__).resolve().parents[2]
TIERS = ("EMPEROR", "MERIT", "BODHI")
MINIMUMS = {"EMPEROR": 5000, "MERIT": 3000, "BODHI": 2000}
STATUSES = (
    "CONFIRMED",
    "REPLACEMENT_CONFIRMED",
    "PENDING",
    "WAITLISTED",
    "CANCELLED",
    "ABSENT",
    "REPLACED",
)
ELIGIBLE = STATUSES[:2]
PREFERENCES = ("contribution_seat", "activeness", "category_zone")
MODES = ("INITIAL", "REGENERATE_DRAFT", "REPAIR_PUBLISHED", "FULL_REGENERATION")
DEFAULT_PREFERENCES = [{"key": k, "enabled": True} for k in PREFERENCES]


class DomainError(ValueError):
    def __init__(self, code, message, details=None):
        super().__init__(message)
        self.code, self.details = code, details or {}


def policy():
    cfg = read_json(ROOT / "config/production_policy.json")
    jsonschema.Draft202012Validator(
        read_json(ROOT / "schemas/production_policy.schema.json")
    ).validate(cfg)
    return cfg


def mapped_weights(preferences, version="ranked-v1"):
    if version != "ranked-v1" or not isinstance(preferences, list):
        raise DomainError("INVALID_INPUT", "Unsupported preference profile")
    if len(preferences) != 3 or any(
        not isinstance(p, dict)
        or set(p) != {"key", "enabled"}
        or type(p["enabled"]) is not bool
        for p in preferences
    ):
        raise DomainError(
            "INVALID_INPUT", "Supply every preference once with a boolean enabled flag"
        )
    if {p["key"] for p in preferences} != set(PREFERENCES):
        raise DomainError(
            "INVALID_INPUT", "Unknown, duplicate or missing preference key"
        )
    result = dict.fromkeys(PREFERENCES, 0)
    active = 0
    for p in preferences:
        if p["enabled"]:
            result[p["key"]] = policy()["rank_weights"][active]
            active += 1
    return result


def map_host_status(value, mapping):
    if value not in mapping or mapping[value] not in STATUSES:
        raise DomainError("INVALID_INPUT", "Unknown host registration status")
    return mapping[value]


def validate_request(request):
    errors = sorted(
        jsonschema.Draft202012Validator(
            read_json(ROOT / "schemas/production_request.schema.json")
        ).iter_errors(request),
        key=lambda e: str(e.path),
    )
    if errors:
        raise DomainError(
            "INVALID_INPUT",
            "Request schema validation failed",
            {"problems": [f"{list(e.path)}: {e.message}" for e in errors[:20]]},
        )
    cfg = policy()
    if request["policy_version_id"] != cfg["policy_version_id"]:
        raise DomainError("INVALID_INPUT", "Unsupported policy version")
    mapped_weights(request["preferences"], request["preference_profile_version"])
    if (
        request["generation_mode"] != "REPAIR_PUBLISHED"
        and request["baseline_plan_version_id"] is not None
    ):
        raise DomainError("INVALID_INPUT", "Only published repair accepts a baseline")
    layout = request["layout"]
    if request["layout_version_id"] != layout["layout_version_id"]:
        raise DomainError("INVALID_INPUT", "Layout version does not match payload")
    if set(layout["accessible_positions"]) != {
        1,
        2,
        layout["seats_per_row"] - 1,
        layout["seats_per_row"],
    }:
        raise DomainError(
            "INVALID_INPUT",
            "Policy requires side positions 1, 2, width-1, width for accessibility",
        )
    seats = layout["seats"]
    width = layout["seats_per_row"]
    rows = layout["row_count"]
    aisle = layout["aisle_after_position"]
    if not 0 < aisle < width or len(seats) != rows * width:
        raise DomainError(
            "INVALID_INPUT", "Layout dimensions/count/aisle are inconsistent"
        )
    if len({s["seat_id"] for s in seats}) != len(seats) or len(
        {(s["row_number"], s["physical_position"]) for s in seats}
    ) != len(seats):
        raise DomainError("INVALID_INPUT", "Duplicate seat ID or physical coordinate")
    for s in seats:
        pos = s["physical_position"]
        row = s["row_number"]
        if (
            not 1 <= row <= rows
            or not 1 <= pos <= width
            or s["row_index"] != row - 1
            or not 1 <= s["priority_rank"] <= width
        ):
            raise DomainError(
                "INVALID_INPUT", "Invalid seat coordinate, rank or row index"
            )
        if s["side"] != ("LEFT" if pos <= aisle else "RIGHT"):
            raise DomainError(
                "INVALID_INPUT", "Seat side contradicts physical coordinate"
            )
        if s["is_accessible"] != (pos in layout["accessible_positions"]):
            raise DomainError(
                "INVALID_INPUT", "Accessibility flags contradict versioned layout"
            )
    if len(set(layout["accessible_positions"])) != len(
        layout["accessible_positions"]
    ) or any(not 1 <= p <= width for p in layout["accessible_positions"]):
        raise DomainError("INVALID_INPUT", "Accessible positions outside layout")
    used = set()
    for a, b in layout["approved_pairs"]:
        if b != a + 1 or a < 1 or b > width or a <= aisle < b or a in used or b in used:
            raise DomainError(
                "INVALID_INPUT",
                "Approved pairs must be disjoint adjacent seats on one side",
            )
        used.update((a, b))
    ids = [p["participant_id"] for p in request["participants"]]
    if len(set(ids)) != len(ids):
        raise DomainError("INVALID_INPUT", "Duplicate participant ID")
    by_id = {p["participant_id"]: p for p in request["participants"]}
    replaced = set()
    for p in request["participants"]:
        if p["contribution_amount_rm"] < cfg["tier_minimums"][p["contribution_tier"]]:
            raise DomainError(
                "INVALID_INPUT",
                "Contribution below selected tier minimum",
                {"participant_id": p["participant_id"]},
            )
        target = p["replacement_for_participant_id"]
        if p["registration_status"] == "REPLACEMENT_CONFIRMED":
            if (
                not target
                or target == p["participant_id"]
                or target not in by_id
                or by_id[target]["registration_status"] != "REPLACED"
                or target in replaced
            ):
                raise DomainError(
                    "INVALID_REPLACEMENT",
                    "Replacement must uniquely reference a REPLACED registration in this event",
                )
            replaced.add(target)
        elif target is not None:
            raise DomainError(
                "INVALID_REPLACEMENT",
                "Only a confirmed replacement may have a replacement link",
            )
    return copy.deepcopy(request)
