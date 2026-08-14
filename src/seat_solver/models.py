"""Typed data models and JSON loading helpers for the seat allocation solver.

All monetary values are integer ringgit. All model-facing quantities are
integers so they can be passed to CP-SAT without floating-point conversion.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0.0"
CASE_STUDY_NAME = "PJ Kwan Inn Teng"

TIER_NAMES = ("EMPEROR", "BODHI", "MERIT")
CATEGORY_NAMES = ("MONASTIC", "COMMITTEE", "VOLUNTEER", "GENERAL_DEVOTEE")
ZONE_NAMES = ("LEFT_OUTER", "LEFT_CENTER", "RIGHT_CENTER", "RIGHT_OUTER")

CATEGORY_IMPORTANCE = {
    "MONASTIC": 4,
    "COMMITTEE": 3,
    "VOLUNTEER": 2,
    "GENERAL_DEVOTEE": 1,
}


class InputDataError(ValueError):
    """Raised when an input JSON document cannot be parsed into a model."""


@dataclass(frozen=True)
class Participant:
    """One primary participant record.

    An Emperor participant represents a two-seat allocation unit; the optional
    ``adjacent_person_name`` only affects seat display names, never the count
    of primary participants.
    """

    participant_id: str
    full_name: str
    is_synthetic: bool
    contribution_amount_rm: int
    contribution_tier: str
    age: int
    is_elderly: bool
    is_monk: bool
    requires_accessible_seat: bool
    participant_category: str
    category_importance: int
    events_joined_last_2_years: int
    adjacent_person_name: str | None
    previous_seat_ids: tuple[str, ...]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Participant":
        try:
            return cls(
                participant_id=str(raw["participant_id"]),
                full_name=str(raw["full_name"]),
                is_synthetic=bool(raw["is_synthetic"]),
                contribution_amount_rm=int(raw["contribution_amount_rm"]),
                contribution_tier=str(raw["contribution_tier"]),
                age=int(raw["age"]),
                is_elderly=bool(raw["is_elderly"]),
                is_monk=bool(raw["is_monk"]),
                requires_accessible_seat=bool(raw["requires_accessible_seat"]),
                participant_category=str(raw["participant_category"]),
                category_importance=int(raw["category_importance"]),
                events_joined_last_2_years=int(raw["events_joined_last_2_years"]),
                adjacent_person_name=(
                    None
                    if raw["adjacent_person_name"] is None
                    else str(raw["adjacent_person_name"])
                ),
                previous_seat_ids=tuple(str(s) for s in raw["previous_seat_ids"]),
            )
        except KeyError as exc:  # pragma: no cover - guarded by schema validation
            raise InputDataError(f"participant record missing field {exc}") from exc

    def to_dict(self) -> dict[str, Any]:
        return {
            "participant_id": self.participant_id,
            "full_name": self.full_name,
            "is_synthetic": self.is_synthetic,
            "contribution_amount_rm": self.contribution_amount_rm,
            "contribution_tier": self.contribution_tier,
            "age": self.age,
            "is_elderly": self.is_elderly,
            "is_monk": self.is_monk,
            "requires_accessible_seat": self.requires_accessible_seat,
            "participant_category": self.participant_category,
            "category_importance": self.category_importance,
            "events_joined_last_2_years": self.events_joined_last_2_years,
            "adjacent_person_name": self.adjacent_person_name,
            "previous_seat_ids": list(self.previous_seat_ids),
        }


@dataclass(frozen=True)
class Seat:
    """One physical seat. ``physical_position`` is the left-to-right position
    (1..16) used for adjacency; ``priority_rank`` is the seat desirability
    rank (1 is best) and must never be used for adjacency.

    A seat carries no tier attribute: tier bands are demand-derived row
    intervals computed in preprocessing, not fixed properties of the venue.
    """

    seat_id: str
    row_number: int
    row_index: int
    physical_position: int
    priority_rank: int
    side: str
    zone: str
    is_accessible: bool
    is_blocked: bool

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Seat":
        return cls(
            seat_id=str(raw["seat_id"]),
            row_number=int(raw["row_number"]),
            row_index=int(raw["row_index"]),
            physical_position=int(raw["physical_position"]),
            priority_rank=int(raw["priority_rank"]),
            side=str(raw["side"]),
            zone=str(raw["zone"]),
            is_accessible=bool(raw["is_accessible"]),
            is_blocked=bool(raw["is_blocked"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "seat_id": self.seat_id,
            "row_number": self.row_number,
            "row_index": self.row_index,
            "physical_position": self.physical_position,
            "priority_rank": self.priority_rank,
            "side": self.side,
            "zone": self.zone,
            "is_accessible": self.is_accessible,
            "is_blocked": self.is_blocked,
        }


@dataclass(frozen=True)
class FloorPlan:
    row_count: int
    seats_per_row: int
    aisle_after_position: int
    seats: tuple[Seat, ...]
    _by_id: dict[str, Seat] = field(default_factory=dict, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_by_id", {seat.seat_id: seat for seat in self.seats})

    @property
    def total_seats(self) -> int:
        return len(self.seats)

    def seat_by_id(self, seat_id: str) -> Seat:
        try:
            return self._by_id[seat_id]
        except KeyError as exc:
            raise InputDataError(f"unknown seat_id {seat_id!r}") from exc

    def has_seat(self, seat_id: str) -> bool:
        return seat_id in self._by_id

    def seats_in_row(self, row_number: int) -> list[Seat]:
        return sorted(
            (s for s in self.seats if s.row_number == row_number),
            key=lambda s: s.physical_position,
        )

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "FloorPlan":
        return cls(
            row_count=int(raw["row_count"]),
            seats_per_row=int(raw["seats_per_row"]),
            aisle_after_position=int(raw["aisle_after_position"]),
            seats=tuple(Seat.from_dict(s) for s in raw["seats"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "row_count": self.row_count,
            "seats_per_row": self.seats_per_row,
            "total_seats": self.total_seats,
            "aisle_after_position": self.aisle_after_position,
            "seats": [seat.to_dict() for seat in self.seats],
        }


@dataclass(frozen=True)
class TierConfig:
    """Contribution boundaries and seat demand of one tier.

    Tiers carry no fixed row interval: the rows a tier occupies (its *band*)
    are derived from the event's tier demand during preprocessing.
    """

    min_contribution_rm: int
    max_contribution_rm: int | None
    seats_required: int

    def contains(self, amount_rm: int) -> bool:
        if amount_rm < self.min_contribution_rm:
            return False
        if (
            self.max_contribution_rm is not None
            and amount_rm > self.max_contribution_rm
        ):
            return False
        return True


@dataclass(frozen=True)
class SolverConfig:
    tiers: dict[str, TierConfig]
    priority_seat_weight: int
    category_zone_weight: int
    movement_weight: int
    activeness_weight: int
    accessible_rank: int
    monk_rank: int
    elderly_rank: int
    default_rank: int
    category_zone_costs: dict[str, dict[str, int]]
    fixed_move_penalty: int
    row_distance_weight: int
    column_distance_weight: int
    emperor_pair_priorities: dict[tuple[int, int], int]
    enforce_front_fill: bool
    enforce_middle_fill: bool
    normalize_penalties: bool
    main_objective_scale: int
    require_optimal: bool
    max_time_seconds: int
    num_search_workers: int
    random_seed: int
    log_search_progress: bool

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "SolverConfig":
        tiers = {
            name: TierConfig(
                min_contribution_rm=int(t["min_contribution_rm"]),
                max_contribution_rm=(
                    None
                    if t["max_contribution_rm"] is None
                    else int(t["max_contribution_rm"])
                ),
                seats_required=int(t["seats_required"]),
            )
            for name, t in raw["tiers"].items()
        }
        weights = raw["weights"]
        rules = raw["desired_priority_rules"]
        movement = raw["movement"]
        pair_priorities: dict[tuple[int, int], int] = {}
        for key, priority in raw["emperor_pair_priorities"].items():
            left, right = key.split("-")
            pair_priorities[(int(left), int(right))] = int(priority)
        solver = raw["solver"]
        return cls(
            tiers=tiers,
            priority_seat_weight=int(weights["priority_seat_weight"]),
            category_zone_weight=int(weights["category_zone_weight"]),
            movement_weight=int(weights["movement_weight"]),
            activeness_weight=int(weights["activeness_weight"]),
            accessible_rank=int(rules["accessible_rank"]),
            monk_rank=int(rules["monk_rank"]),
            elderly_rank=int(rules["elderly_rank"]),
            default_rank=int(rules["default_rank"]),
            category_zone_costs={
                cat: {zone: int(cost) for zone, cost in costs.items()}
                for cat, costs in raw["category_zone_costs"].items()
            },
            fixed_move_penalty=int(movement["fixed_move_penalty"]),
            row_distance_weight=int(movement["row_distance_weight"]),
            column_distance_weight=int(movement["column_distance_weight"]),
            emperor_pair_priorities=pair_priorities,
            enforce_front_fill=bool(raw["constraints"]["enforce_front_fill"]),
            enforce_middle_fill=bool(raw["constraints"]["enforce_middle_fill"]),
            normalize_penalties=bool(raw["constraints"]["normalize_penalties"]),
            main_objective_scale=int(raw["tie_break"]["main_objective_scale"]),
            require_optimal=bool(solver["require_optimal"]),
            max_time_seconds=int(solver["max_time_seconds"]),
            num_search_workers=int(solver["num_search_workers"]),
            random_seed=int(solver["random_seed"]),
            log_search_progress=bool(solver["log_search_progress"]),
        )

    def weights_dict(self) -> dict[str, int]:
        return {
            "priority_seat_weight": self.priority_seat_weight,
            "category_zone_weight": self.category_zone_weight,
            "movement_weight": self.movement_weight,
            "activeness_weight": self.activeness_weight,
        }

    def tier_for_contribution(self, amount_rm: int) -> str | None:
        for name, tier in self.tiers.items():
            if tier.contains(amount_rm):
                return name
        return None


@dataclass(frozen=True)
class PreviousAllocation:
    """Mapping of participant_id to the seat ids used in the previous event."""

    allocations: dict[str, tuple[str, ...]]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "PreviousAllocation":
        allocations: dict[str, tuple[str, ...]] = {}
        for entry in raw["allocations"]:
            allocations[str(entry["participant_id"])] = tuple(
                str(s) for s in entry["seat_ids"]
            )
        return cls(allocations=allocations)

    def seats_for(self, participant_id: str) -> tuple[str, ...]:
        return self.allocations.get(participant_id, ())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "allocations": [
                {"participant_id": pid, "seat_ids": list(seats)}
                for pid, seats in self.allocations.items()
            ],
        }


def read_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: str | Path, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def load_participants(path: str | Path) -> list[Participant]:
    raw = read_json(path)
    if not isinstance(raw, dict) or "participants" not in raw:
        raise InputDataError("participants file must contain a 'participants' array")
    return [Participant.from_dict(item) for item in raw["participants"]]


def load_floor_plan(path: str | Path) -> FloorPlan:
    return FloorPlan.from_dict(read_json(path))


def load_solver_config(path: str | Path) -> SolverConfig:
    return SolverConfig.from_dict(read_json(path))


def load_previous_allocation(path: str | Path) -> PreviousAllocation:
    return PreviousAllocation.from_dict(read_json(path))
