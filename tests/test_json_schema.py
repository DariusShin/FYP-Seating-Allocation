"""JSON Schema conformance and output display-name contract tests."""

from __future__ import annotations

from seat_solver.validator import validate_against_schema


def test_participants_file_matches_schema(participants_payload):
    assert (
        validate_against_schema(participants_payload, "participant.schema.json") == []
    )


def test_floor_plan_file_matches_schema(floor_plan_payload):
    assert validate_against_schema(floor_plan_payload, "floor_plan.schema.json") == []


def test_solver_config_matches_schema(config_payload):
    assert validate_against_schema(config_payload, "solver_config.schema.json") == []


def test_result_matches_schema(default_result):
    assert validate_against_schema(default_result, "solver_result.schema.json") == []


def test_error_result_matches_schema(floor_plan, config):
    from seat_solver.solver import solve_seat_allocation

    from conftest import make_participant

    participants = [
        make_participant(f"P{i:03d}", "EMPEROR", 2000 + i) for i in range(1, 118)
    ]
    result = solve_seat_allocation(participants, floor_plan, config, None)
    assert result["status"] == "error"
    assert validate_against_schema(result, "solver_result.schema.json") == []


def test_emperor_without_guest_shows_primary_name_on_both_seats(
    default_result, participants
):
    by_id = {p.participant_id: p for p in participants}
    checked = 0
    for assignment in default_result["assignments"]:
        participant = by_id[assignment["participant_id"]]
        if assignment["allocation_type"] != "EMPEROR_PAIR":
            continue
        if participant.adjacent_person_name is not None:
            continue
        names = [seat["display_name"] for seat in assignment["seats"]]
        assert names == [participant.full_name, participant.full_name]
        checked += 1
    assert checked == 43


def test_emperor_with_guest_shows_both_names(default_result, participants):
    by_id = {p.participant_id: p for p in participants}
    checked = 0
    for assignment in default_result["assignments"]:
        participant = by_id[assignment["participant_id"]]
        if assignment["allocation_type"] != "EMPEROR_PAIR":
            continue
        if participant.adjacent_person_name is None:
            continue
        seats = assignment["seats"]
        names = {seat["display_name"] for seat in seats}
        assert names == {participant.full_name, participant.adjacent_person_name}
        # The primary participant takes the better-ranked seat of the pair.
        best = min(seats, key=lambda seat: seat["priority_rank"])
        assert best["display_name"] == participant.full_name
        checked += 1
    assert checked == 43


def test_floor_plan_section_mirrors_assignments(default_result):
    seat_owner = {
        seat_id: assignment["participant_id"]
        for assignment in default_result["assignments"]
        for seat_id in assignment["seat_ids"]
    }
    for row in default_result["floor_plan"]["rows"]:
        for seat in row["seats"]:
            if seat["occupancy_status"] == "OCCUPIED":
                assert seat["participant_id"] == seat_owner[seat["seat_id"]]
                assert seat["display_name"]
            else:
                assert seat["participant_id"] is None
                assert seat["seat_id"] not in seat_owner
