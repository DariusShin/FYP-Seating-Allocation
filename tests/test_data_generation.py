"""Tests for the deterministic mock participant generator."""

from __future__ import annotations

import random

from seat_solver.data_generator import (
    DEFAULT_SEED,
    build_previous_allocation,
    generate_participants,
)
from seat_solver.floor_plan_generator import generate_floor_plan


def test_exactly_122_primary_records(participants):
    assert len(participants) == 122
    assert len({p.participant_id for p in participants}) == 122


def test_tier_distribution(participants):
    tiers = [p.contribution_tier for p in participants]
    assert tiers.count("EMPEROR") == 86
    assert tiers.count("BODHI") == 12
    assert tiers.count("MERIT") == 24


def test_seat_demand_is_208(participants):
    demand = sum(2 if p.contribution_tier == "EMPEROR" else 1 for p in participants)
    assert demand == 208


def test_contributions_match_tier_boundaries(participants, config):
    for p in participants:
        assert config.tiers[p.contribution_tier].contains(p.contribution_amount_rm)


def test_dataset_diversity(participants):
    assert sum(1 for p in participants if p.is_monk) >= 4
    assert sum(1 for p in participants if p.is_elderly and p.age >= 60) >= 20
    assert sum(1 for p in participants if p.requires_accessible_seat) >= 5
    events = [p.events_joined_last_2_years for p in participants]
    assert min(events) == 0
    assert max(events) >= 20


def test_monk_flag_matches_monastic_category(participants):
    for p in participants:
        assert p.is_monk == (p.participant_category == "MONASTIC")


def test_emperor_adjacent_names_split_half(participants):
    """Half the Emperors carry a guest name (two-name pairs); half do not
    (merged-cell display of the primary name on both seats)."""
    emperors = [p for p in participants if p.contribution_tier == "EMPEROR"]
    named = [p for p in emperors if p.adjacent_person_name is not None]
    assert len(emperors) == 86
    assert len(named) == 43
    assert len(emperors) - len(named) == 43
    assert len({p.adjacent_person_name for p in named}) == 43


def test_previous_allocation_coverage_and_uniqueness(participants):
    with_previous = [p for p in participants if p.previous_seat_ids]
    assert len(with_previous) == 85  # ~70% of 122
    used = [seat for p in with_previous for seat in p.previous_seat_ids]
    assert len(used) == len(set(used)), "previous allocation reuses a physical seat"
    for p in with_previous:
        expected = 2 if p.contribution_tier == "EMPEROR" else 1
        assert len(p.previous_seat_ids) == expected


def test_generation_is_deterministic():
    first = [p.to_dict() for p in generate_participants(seed=DEFAULT_SEED)]
    second = [p.to_dict() for p in generate_participants(seed=DEFAULT_SEED)]
    assert first == second

    plan = generate_floor_plan()
    prev_a = build_previous_allocation(
        generate_participants(seed=DEFAULT_SEED), plan, random.Random(DEFAULT_SEED + 1)
    )
    prev_b = build_previous_allocation(
        generate_participants(seed=DEFAULT_SEED), plan, random.Random(DEFAULT_SEED + 1)
    )
    assert prev_a == prev_b
