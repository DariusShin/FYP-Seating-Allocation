"""Extract masked PJKIT history, then build separate solver-input candidates.

Extraction needs openpyxl; building/validation uses the project's solver environment.
Source names, phone numbers and remarks are never written to the output directory.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import copy
import csv
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import random
import re
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[2]
YEARS = tuple(range(2021, 2027))
EXPECTED = {2021: 91, 2022: 103, 2023: 114, 2024: 105, 2025: 126, 2026: 60}
TIERS = {"梁皇功德主": "EMPEROR", "福慧功德主": "MERIT", "菩提功德主": "BODHI"}
MINIMUMS = {"EMPEROR": 5000, "MERIT": 3000, "BODHI": 2000}
SEED = 20261020
VERSION = "pjkit-source-informed-v1-2026-10-20"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def display_key(value):
    """User-specified first name token, with the family suffix removed.

    This is a provisional grouping key, not verified person identification.
    Unusual short/long tokens are explicitly retained for supervisor review.
    """
    text = unicodedata.normalize("NFKC", str(value or "")).replace("\u200b", "").strip()
    text = text.split("合家", 1)[0].strip()
    return re.split(r"\s+", text)[0] if text else ""


def phone_key(value):
    if value is None or str(value).strip() in ("", "-", "—"):
        return None
    if isinstance(value, (int, float)):
        value = str(int(value)) if float(value).is_integer() else str(value)
    text = unicodedata.normalize("NFKC", str(value)).strip()
    # Match whole contact cells only: no country-code guessing or splitting
    # multi-phone cells. Phones support review, never automatic name merging.
    return re.sub(r"[\s()+.-]", "", text)


def integer(value, location):
    try:
        number = Decimal(str(value))
        if not number.is_finite() or number < 0 or number != int(number):
            raise ValueError
        return int(number)
    except Exception:
        raise ValueError(f"Invalid nonnegative integer at {location}") from None


def activity(year_counts, target_year):
    previous = (target_year - 2, target_year - 1)
    return {"target_year": target_year,
            "actual_prior_two_year_distinct_event_count": sum(year_counts.get(y, 0) > 0 for y in previous),
            "actual_prior_two_year_registration_count": sum(year_counts.get(y, 0) for y in previous),
            "unobserved_lookback_years": [y for y in previous if y not in YEARS],
            "full_history_registration_count": sum(year_counts.values()),
            "full_history_distinct_event_year_count": sum(n > 0 for n in year_counts.values())}


def raw_rows(workbook):
    import openpyxl  # Extraction-only dependency; never required by the solver.
    wb = openpyxl.load_workbook(workbook, read_only=True, data_only=True)
    try:
        if set(wb.sheetnames) != set(map(str, YEARS)):
            raise ValueError("Expected exactly the six 2021–2026 sheets")
        result = []
        for year in YEARS:
            values = iter(wb[str(year)].values)
            headers = [str(v or "").strip() for v in next(values)]
            cols = {label: headers.index(label) for label in ("陽上名字", "功德主/祈福/燈籠/供齋/超度", "RM", "PHONE")}
            for row_number, row in enumerate(values, 2):
                name = row[cols["陽上名字"]]
                if name is None or not str(name).strip():
                    continue
                key = display_key(name)
                if not key:
                    raise ValueError(f"Empty display-name key at {year}:{row_number}")
                tier = str(row[cols["功德主/祈福/燈籠/供齋/超度"]] or "").strip()
                if tier not in TIERS:
                    raise ValueError(f"Unmapped contribution tier at {year}:{row_number}")
                result.append({"year": year, "row": row_number, "name": str(name).strip(), "key": key,
                               "phone": phone_key(row[cols["PHONE"]]),
                               "phone_raw": str(row[cols["PHONE"]] or "").strip(),
                               "phone_was_numeric": isinstance(row[cols["PHONE"]], (int, float)),
                               "tier": TIERS[tier], "amount": integer(row[cols["RM"]], f"{year}:J{row_number}")})
        if Counter(r["year"] for r in result) != Counter(EXPECTED):
            raise ValueError("Workbook row counts differ from the supplied 599-registration controls")
        return result
    finally:
        wb.close()


def summary_rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.reader(stream))
    header = next(i for i, row in enumerate(rows) if "REGISTRANT NAME (陽上名字)" in row)
    h = rows[header]
    result = []
    for number, row in enumerate(rows[header + 1:], header + 2):
        if len(row) <= 1 or not row[1].strip().isdigit():
            continue
        counts = {y: integer(row[h.index(str(y))] or 0, f"summary:{number}:{y}") for y in YEARS}
        total = integer(row[h.index("6-YR TOTAL (出席次數)")], f"summary:{number}:total")
        if sum(counts.values()) != total:
            raise ValueError(f"Summary total does not reconcile at row {number}")
        result.append({"row": number, "key": display_key(row[h.index("REGISTRANT NAME (陽上名字)")]),
                       "year_counts": counts, "total": total})
    return result


def privacy_check(directory, rows):
    """Inspect serialized JSON without persisting a real-to-demo identifier map."""
    forbidden_names = {r["name"] for r in rows} | {r["key"] for r in rows}
    forbidden_phones = {r["phone"] for r in rows if r["phone"] and len(r["phone"]) >= 7}
    for path in Path(directory).rglob("*.json"):
        text = path.read_text(encoding="utf-8")
        if any(name in text for name in forbidden_names) or any(phone in text for phone in forbidden_phones):
            raise ValueError(f"Source identifier leakage detected in {path.name}")


def extract(workbook, summary, out):
    rows, summaries = raw_rows(workbook), summary_rows(summary)
    groups = defaultdict(list)
    for row in rows:
        groups[row["key"]].append(row)
    labels = list(range(1, len(groups) + 1))
    random.Random(SEED).shuffle(labels)
    pids = {key: f"DEMO-P{label:04d}" for key, label in zip(groups, labels)}
    contacts = {phone: f"DEMO-CONTACT-{i:04d}" for i, phone in enumerate(dict.fromkeys(r["phone"] for r in rows if r["phone"]), 1)}
    by_phone = defaultdict(set)
    for row in rows:
        if row["phone"]:
            by_phone[contacts[row["phone"]]].add(pids[row["key"]])
    summary_counts = Counter()
    for row in summaries:
        for year, count in row["year_counts"].items():
            summary_counts[row["key"], year] += count
    actual_counts = Counter((r["key"], r["year"]) for r in rows)
    if any(summary_counts[key] != actual_counts[key] for key in summary_counts.keys() | actual_counts.keys()):
        raise ValueError("Summary and workbook disagree after display-name normalization; review before export")
    participants, registrations, checks, reviews = [], [], [], []
    for key, members in groups.items():
        pid = pids[key]
        counts = Counter(r["year"] for r in members)
        participant = {"person_id": pid, "display_name": f"Demo Participant {pid}",
                       "year_registration_counts": {str(y): counts[y] for y in YEARS},
                       "full_history_registration_count": len(members),
                       "full_history_distinct_event_year_count": len(counts),
                       "demo_contact_ids": sorted({contacts[r["phone"]] for r in members if r["phone"]}),
                       "missing_contact_registration_count": sum(not r["phone"] for r in members),
                       "source_name_variant_count": len({r["name"] for r in members}),
                       "identity_status": "provisional_display_name_group_not_verified_person",
                       "activity_by_target_year": {str(y): activity(counts, y) for y in YEARS}}
        participants.append(participant)
        reasons = []
        if participant["source_name_variant_count"] > 1:
            reasons.append("multiple_original_name_strings_share_display_key")
        if len(key) not in (3, 4):
            reasons.append("unusual_display_token_length_requires_manual_review")
        if max(counts.values()) > 1:
            reasons.append("multiple_registrations_in_one_annual_event")
        if reasons:
            reviews.append({"person_id": pid, "reasons": reasons,
                            "source_rows": [{"sheet": str(r["year"]), "row": r["row"]} for r in members]})
        checks.append({"person_id": pid, "workbook_year_counts": participant["year_registration_counts"],
                       "summary_year_counts": {str(y): summary_counts[key, y] for y in YEARS},
                       "summary_rows": [r["row"] for r in summaries if r["key"] == key], "passed": True})
        for row in members:
            minimum = MINIMUMS[row["tier"]]
            registrations.append({"registration_id": f"DEMO-R{row['year']}-{row['row'] - 1:04d}",
                                  "person_id": pid, "display_name": participant["display_name"], "year": row["year"],
                                  "source": {"sheet": str(row["year"]), "row": row["row"]},
                                  "demo_contact_id": contacts.get(row["phone"]),
                                  "source_phone_cell_was_numeric": row["phone_was_numeric"],
                                  "contribution_tier": row["tier"], "source_amount_rm": row["amount"],
                                  "tier_amount_valid": row["amount"] >= minimum,
                                  "synthetic_amount_rm": max(row["amount"], minimum),
                                  "synthetic_amount_correction": row["amount"] < minimum,
                                  "event_activeness_score": len(members),
                                  "score_definition": "full_2021_2026_registration_total_by_provisional_display_name_group",
                                  "actual_prior_two_year_history": activity(counts, row["year"])})
    registrations.sort(key=lambda r: (r["year"], r["source"]["row"]))
    corrections = [{k: r[k] for k in ("registration_id", "person_id", "source", "source_amount_rm", "synthetic_amount_rm")}
                   for r in registrations if r["synthetic_amount_correction"]]
    out.mkdir(parents=True, exist_ok=False)
    save(out / "history/participants.json", sorted(participants, key=lambda p: p["person_id"]))
    save(out / "history/registrations.json", registrations)
    save(out / "history/summary-reconciliation.json", {"passed": True, "summary_registrant_rows": len(summaries), "groups": checks})
    save(out / "history/identity-review.json", {"name_groups": reviews,
         "shared_contact_groups": [{"demo_contact_id": k, "person_ids": sorted(v), "automatic_merge": False}
                                   for k, v in by_phone.items() if len(v) > 1]})
    save(out / "data-quality.json", {"registration_count": len(rows), "year_counts": EXPECTED,
         "raw_name_string_count": len({r["name"] for r in rows}),
         "raw_name_phone_combination_count": len({(r["name"], r["phone_raw"]) for r in rows}),
         "provisional_display_name_groups": len(groups), "summary_registrant_rows": len(summaries),
         "missing_phone_registrations": sum(not r["phone"] for r in rows),
         "shared_contact_groups": sum(len(v) > 1 for v in by_phone.values()),
         "duplicate_person_year_excess_registrations": sum(n - 1 for n in actual_counts.values() if n > 1),
         "tier_amount_corrections": corrections, "supervisor_identity_review_pending": True})
    save(out / "manifest.json", {"dataset_version": VERSION, "created_at": datetime.now(timezone.utc).isoformat(),
         "status": "masked_history_extracted", "seed": SEED,
         "sources": [{"file": p.name, "sha256": sha(p)} for p in (workbook, summary)],
         "source_data_type": "pseudonymized_source_derived_history_not_fully_synthetic_or_irreversibly_anonymous",
         "privacy": {"real_names_exported": False, "real_phones_exported": False, "real_to_demo_map_saved": False,
                     "note": "Private source rows, amounts and trajectories can permit reidentification; controlled review use only"},
         "activity_override": {"approved_by_user": True, "solver_field": "events_joined_last_2_years",
             "encoded_value": "full_2021_2026_registration_total", "actual_two_year_setting_changed": False,
             "retrospective_prediction_claim_permitted": False,
             "note": "Full-history synthetic proxy deliberately includes later years; not a literal two-year measure"},
         "synthetic_merit_amount_correction_approved_by_user": True,
         "identity_rule": "NFKC, remove zero-width spaces, strip family suffix, first whitespace token; name-primary, phone-review-only",
         "supervisor_approval_status": "pending", "benchmark_protocol_adoption": "not_automatically_adopted"})
    privacy_check(out, rows)
    print(f"Exported {len(rows)} masked registrations and {len(groups)} provisional name groups; summary reconciles.")


def build(out):
    sys.path[:0] = [str(ROOT / "services/seating/src"), str(ROOT)]
    os.environ["SEAT_SOLVER_ROOT"] = str(ROOT)
    os.environ["SEAT_SOLVER_RESOURCES"] = str(ROOT / "services/seating")
    from seat_solver.production.policy import validate_request
    from seat_solver.production.production_validator import validate_placements
    from research.fixtures.synthetic_participants import generate
    from research.experiments.solver_benchmark.cases import witness

    manifest = read(out / "manifest.json")
    if manifest["status"] != "masked_history_extracted" or (out / "requests").exists():
        raise ValueError("Build requires a freshly extracted bundle; never overwrite generated requests")
    rows = read(out / "history/registrations.json")
    records, provenance = [], {}

    def persist(name, request, kind, assumptions):
        request.pop("attendance", None)
        request["generation_mode"] = "INITIAL"
        request["event_id"] = "PJKIT-DEMO-" + name.upper().replace("/", "-")
        request["event_details"] = {"name": "Synthetic PJKIT " + name, "date": None, "time": None,
                                    "timezone": "Asia/Kuala_Lumpur", "venue": "Prototype synthetic venue; historical layout not verified"}
        request = validate_request(request)
        proof = witness(request)
        if not validate_placements(request, proof["placements"])["passed"]:
            raise ValueError("Constructive witness failed independent validation")
        path = out / "requests" / f"{name}.json"
        save(path, request)
        save(out / "witnesses" / f"{name}.json", proof)
        records.append({"case_id": name, "kind": kind, "input": str(path.relative_to(out)),
                        "sha256": sha(path), "registrations": len(request["participants"]),
                        "tier_counts": dict(Counter(p["contribution_tier"] for p in request["participants"])),
                        "physical_seat_demand": sum(2 if p["contribution_tier"] == "EMPEROR" else 1 for p in request["participants"]),
                        "feasibility_witness_valid": True, "assumptions": assumptions})
        return request, proof

    defaults = ["CONFIRMED is an assumed synthetic paid status, not observed payment or attendance",
                "age=40 is a required-schema placeholder; role=GENERAL_DEVOTEE and accessibility=false are defaults, not observed facts",
                "same existing 232-seat layout; historical layouts and accessibility needs were not provided",
                "full-history total intentionally encoded in the existing two-year-named field; cross-sectional synthetic cohort only"]
    yearly = {}
    for year in YEARS:
        request = generate(0, 0, 0, seed=SEED)
        members = [r for r in rows if r["year"] == year]
        request["participants"] = [{"participant_id": r["registration_id"], "full_name": r["display_name"],
             "registration_status": "CONFIRMED", "contribution_tier": r["contribution_tier"],
             "contribution_amount_rm": r["synthetic_amount_rm"], "requires_accessible_seat": False,
             "participant_category": "GENERAL_DEVOTEE", "events_joined_last_2_years": r["event_activeness_score"],
             "age": 40, "adjacent_person_name": None} for r in members]
        yearly[year], _ = persist(f"yearly/{year}", request, "masked_year_cohort_with_declared_synthetic_defaults", defaults)
        provenance[str(year)] = [{"registration_id": r["registration_id"], "person_id": r["person_id"],
                                 "activity_value": r["event_activeness_score"],
                                 "amount_correction": r["synthetic_amount_correction"]} for r in members]
    prototype = copy.deepcopy(yearly[2026])
    rng = random.Random(SEED)
    roles = ["MONASTIC", "COMMITTEE", "VOLUNTEER", "GENERAL_DEVOTEE"]
    for person in prototype["participants"]:
        person["participant_category"] = rng.choice(roles)
        person["age"] = rng.randrange(18, 90)
    persist("prototype-2026", prototype, "prototype_demo_with_simulated_roles_and_ages",
            defaults + ["role and age fields deliberately replaced with seeded simulated values to exercise the prototype"])

    calibration = {tier: [r["event_activeness_score"] for r in rows if r["year"] == 2026 and r["contribution_tier"] == tier]
                   for tier in MINIMUMS}
    sizes = {"small": (8, 8, 8), "typical": (56, 24, 16), "full": (80, 40, 32), "heavy": (99, 19, 13)}
    for index, (size, counts) in enumerate(sizes.items()):
        base = generate(*counts, seed=SEED + index)
        rng = random.Random(SEED + index)
        for i, p in enumerate(base["participants"], 1):
            p["participant_id"] = f"SYN-{size.upper()}-{i:04d}"
            p["full_name"] = "Demo Participant " + p["participant_id"]
            p["events_joined_last_2_years"] = rng.choice(calibration[p["contribution_tier"]])
        assumptions = ["activity sampled with replacement from the 2026 cohort's tier-conditional full-history frequency distribution",
                       "sizes and tier mix are declared controlled scenarios, not estimates of PJKIT's population",
                       "within-tier contribution increments, uniform role choices and ages are simulated; no such variation/roles were measured",
                       "no individual source identity or historical trajectory copied into these independently generated participants"]
        mixed = None
        for pattern in (("mixed",) if size == "heavy" else ("mixed", "conflict", "tied")):
            request = copy.deepcopy(base)
            for p in request["participants"]:
                if pattern == "tied":
                    p["contribution_amount_rm"] = MINIMUMS[p["contribution_tier"]]
                elif pattern == "conflict":
                    p["contribution_amount_rm"] = MINIMUMS[p["contribution_tier"]] + 100 * (max(calibration[p["contribution_tier"]]) - p["events_joined_last_2_years"])
            persisted, proof = persist(f"controlled/{size}-{pattern}", request, "distribution_sampled_synthetic_stress_case", assumptions + ["pattern=" + pattern])
            if pattern == "mixed":
                mixed = (persisted, proof)
        if size != "heavy":
            request, proof = copy.deepcopy(mixed)
            seats = {s["seat_id"]: s for s in request["layout"]["seats"]}
            candidates = sorted(a["participant_id"] for a in proof["placements"] if all(seats[s]["is_accessible"] for s in a["seat_ids"]))
            selected = set(candidates[:max(1, len(request["participants"]) // 10)])
            if not selected:
                raise ValueError("No witness-supported accessibility candidate")
            for p in request["participants"]:
                p["requires_accessible_seat"] = p["participant_id"] in selected
            persist(f"controlled/{size}-accessible", request, "distribution_sampled_synthetic_stress_case",
                    assumptions + ["accessibility requirements assigned only to witness-compatible synthetic IDs; not an observed prevalence"])
    save(out / "field-provenance.json", {"yearly_registration_links": provenance,
         "prototype": "requests/prototype-2026.json copies the 2026 cohort and simulates only role/age",
         "unobserved_fields": ["paid status", "age", "participant_category", "accessibility", "historical layout", "actual attendance"],
         "phone_tokens": "history-only, non-dialable test identifiers; not solver fields or real SMS/login accounts"})
    save(out / "experiment-catalog.json", {"dataset_version": VERSION, "cases": records,
         "activity_calibration_histograms_2026_by_tier": {k: dict(Counter(v)) for k, v in calibration.items()},
         "solver_benchmark_candidate_cases": [r["case_id"] for r in records if r["case_id"].startswith("controlled/")],
         "weighting_candidate_cases": [r["case_id"] for r in records if r["case_id"].startswith("controlled/") and "heavy" not in r["case_id"]],
         "adoption": "Candidate data only: frozen benchmark runner still generates its original inputs; protocol update and fresh pilot required before adoption"})
    manifest.update(status="built_and_schema_witness_validated", request_count=len(records),
                    generation_script_sha256=sha(__file__),
                    generation_git_revision=__import__("subprocess").check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                    solver_request_schema_sha256=sha(ROOT / "services/seating/schemas/production_request.schema.json"),
                    production_policy_sha256=sha(ROOT / "services/seating/config/production_policy.json"),
                    source_workbooks_copied=False, solver_or_benchmark_executed=False)
    manifest["generated_files_sha256"] = {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob("*.json")) if p.name != "manifest.json"}
    save(out / "manifest.json", manifest)
    print(f"Built {len(records)} schema-valid requests and independently audited constructive witnesses; no solver executed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("extract", "build", "privacy-check"))
    parser.add_argument("--workbook", type=Path)
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.command in ("extract", "privacy-check") and not args.workbook:
        parser.error("--workbook is required for extraction/privacy verification")
    if args.command == "extract":
        if not args.summary:
            parser.error("--summary is required for extraction")
        extract(args.workbook, args.summary, args.out)
    elif args.command == "build":
        build(args.out)
    else:
        privacy_check(args.out, raw_rows(args.workbook))
        print("Privacy check passed: no source names or source phone identifiers found in generated JSON.")


if __name__ == "__main__":
    main()
