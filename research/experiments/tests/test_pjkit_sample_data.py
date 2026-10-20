from collections import Counter
import csv

import pytest

from research.fixtures.pjkit_sample_data import (activity, build, display_key, integer,
                                               phone_key, privacy_check, read, save, summary_rows)


def test_display_name_rule_does_not_truncate_unspaced_names():
    assert display_key("測試甲 測試乙合家") == "測試甲"
    assert display_key("測試甲合家") == "測試甲"
    assert display_key("  測試甲\u3000測試乙合家 ") == "測試甲"
    assert display_key("甲乙丙丁戊己") == "甲乙丙丁戊己"
    assert display_key("甲 乙丙丁") == "甲"  # Deliberate review flag, no invented identity repair.


def test_phone_normalization_never_invents_country_codes_or_missing_contacts():
    assert phone_key(None) is None
    assert phone_key("—") is None
    assert phone_key("+99 (12) 345-6789") == "99123456789"
    assert phone_key(12345678.0) == "12345678"
    assert phone_key("0012/0034") == "0012/0034"


def test_actual_lookback_excludes_current_and_future_but_proxy_preserves_all_rows():
    counts = {2021: 1, 2022: 2, 2023: 1, 2024: 0, 2025: 1, 2026: 1}
    result = activity(counts, 2023)
    assert result["actual_prior_two_year_distinct_event_count"] == 2
    assert result["actual_prior_two_year_registration_count"] == 3
    assert result["full_history_registration_count"] == 6
    assert result["full_history_distinct_event_year_count"] == 5
    assert activity(counts, 2021)["unobserved_lookback_years"] == [2019, 2020]


def test_summary_reader_validates_registration_totals(tmp_path):
    path = tmp_path / "summary.csv"
    headers = ["", "NO.", "REGISTRANT NAME (陽上名字)", "PHONE (電話)", "6-YR TOTAL (出席次數)"] + list(map(str, range(2021, 2027)))
    with path.open("w", newline="") as stream:
        csv.writer(stream).writerows([headers, ["", "1", "測試甲合家", "", "2", "1", "0", "0", "0", "0", "1"]])
    row = summary_rows(path)[0]
    assert row["key"] == "測試甲" and row["total"] == 2
    assert row["year_counts"][2021] == 1
    with pytest.raises(ValueError):
        integer(1.5, "test-row")


def test_source_identifier_leakage_is_rejected(tmp_path):
    rows = [{"name": "測試甲", "key": "測試甲", "phone": "99123456789"}]
    save(tmp_path / "example.json", {"name": "Demo Participant DEMO-P0001", "contact": "DEMO-CONTACT-0001"})
    privacy_check(tmp_path, rows)
    save(tmp_path / "bad.json", {"phone": "99123456789"})
    with pytest.raises(ValueError, match="identifier leakage"):
        privacy_check(tmp_path, rows)


def test_build_preserves_registration_units_proxy_and_corrected_amount_without_solving(tmp_path, monkeypatch):
    from seat_solver.production import production
    def forbidden(*args, **kwargs):
        raise AssertionError("Dataset preparation must not execute a solver")
    monkeypatch.setattr(production, "solve", forbidden)
    rows = []
    for index, (tier, amount) in enumerate((("EMPEROR", 5000), ("MERIT", 3000), ("BODHI", 2000)), 1):
        rows.append({"year": 2026, "registration_id": f"TEST-R{index}", "person_id": f"TEST-P{index}",
                     "display_name": f"Demo Person {index}", "contribution_tier": tier,
                     "synthetic_amount_rm": amount, "event_activeness_score": index + 3,
                     "synthetic_amount_correction": tier == "MERIT"})
    save(tmp_path / "history/registrations.json", rows)
    save(tmp_path / "manifest.json", {"status": "masked_history_extracted"})
    build(tmp_path)
    catalog = read(tmp_path / "experiment-catalog.json")
    assert len(catalog["cases"]) == 20
    assert len(catalog["solver_benchmark_candidate_cases"]) == 13
    assert len(catalog["weighting_candidate_cases"]) == 12
    request = read(tmp_path / "requests/yearly/2026.json")
    assert [p["events_joined_last_2_years"] for p in request["participants"]] == [4, 5, 6]
    assert request["participants"][1]["contribution_amount_rm"] == 3000
    heavy = read(tmp_path / "requests/controlled/heavy-mixed.json")
    assert Counter(p["contribution_tier"] for p in heavy["participants"]) == {"EMPEROR": 99, "MERIT": 19, "BODHI": 13}
    assert all(c["feasibility_witness_valid"] for c in catalog["cases"])
    assert read(tmp_path / "manifest.json")["solver_or_benchmark_executed"] is False
    with pytest.raises(ValueError, match="freshly extracted"):
        build(tmp_path)
