# PJKIT source-informed data candidates

Prepared: 20 October 2026, Asia/Kuala_Lumpur. Dataset version: `pjkit-source-informed-v1-2026-10-20`.

Status: **generated, reconciled, schema checked and constructively feasibility checked; industry-supervisor review pending**. No solver or benchmark experiment was executed to create this bundle. The original benchmark inputs/protocol have not been replaced. The [preparation guide](../README.md) gives reproducible extraction/build commands.

## What is included

| Location | Contents |
|---|---|
| `history/registrations.json` | All 599 source registration rows with replacement names/contact tokens, year/row references, original amounts, separately declared synthetic corrections and activity derivations |
| `history/participants.json` | 196 provisional display-name groups with year counts, full-history totals, genuine prior-two-year counts and masked contact links |
| `history/summary-reconciliation.json` | Group-by-year agreement between the workbook and supplied summary CSV |
| `history/identity-review.json` | Name-variant groups, unusual tokens, repeat registrations and shared contacts for private supervisor checking |
| `data-quality.json` | Source count reconciliation and the single tier/amount exception |
| `requests/yearly/2021.json` … `2026.json` | Six solver-contract-compatible source-count-matched synthetic cohorts |
| `requests/prototype-2026.json` | 60-registration prototype demo based on the 2026 cohort, with explicitly simulated role and age values |
| `requests/controlled/*.json` | 13 independently generated controlled synthetic cases; the 12 non-heavy cases are also candidate inputs for the weighting study |
| `witnesses/` | Constructive complete placements and independent policy audits for every request; these are feasibility certificates, not optimized seating results or solver hints |
| `field-provenance.json` | Registration-to-person links and explicit observed/defaulted/simulated field explanations |
| `experiment-catalog.json` | Request paths, counts, hashes, feasibility status, calibration histograms and scenario assumptions |
| `manifest.json` | Source-file hashes, generator seed/hash, policy/schema hashes and the activity-proxy override |

## Yearly coverage

| Year | Emperor | Merit | Bodhi | Registrations | Physical-seat demand |
|---|---:|---:|---:|---:|---:|
| 2021 | 42 | 30 | 19 | 91 | 133 |
| 2022 | 43 | 31 | 29 | 103 | 146 |
| 2023 | 52 | 32 | 30 | 114 | 166 |
| 2024 | 44 | 31 | 30 | 105 | 149 |
| 2025 | 53 | 37 | 36 | 126 | 179 |
| 2026 | 22 | 17 | 21 | 60 | 82 |
| Total | 256 | 178 | 165 | 599 | 855 across separate events |

One Emperor registration requires two seats; Merit/Bodhi require one. These are sample counts, not confirmed complete annual populations. In particular, the smaller 2026 sample is not extrapolated into a full-year attendance estimate. All six request cohorts use the current prototype's 232-seat layout as a declared assumption; historical layouts were not supplied.

## Identity and privacy treatment

There are **221 original name strings**, **295 original name/phone combinations**, and **219 registrant rows in the supplied summary CSV**. These are different units. Applying the requested display-name rule yields **196 provisional name groups**, not 196 independently verified people.

The rule applies Unicode normalization, removes zero-width spaces and the `合家` suffix/tail, then selects the first whitespace-separated name token. It never arbitrarily truncates an unspaced long Chinese string to three characters. Short/long tokens, merged name variants and four same-year excess registration rows are flagged for review. Namesakes and abbreviations cannot be resolved conclusively from these columns alone. Each registration retains its own ID, so no registration row is lost when person-history groups are formed.

Names are replaced with obvious `Demo Participant DEMO-P....` labels. Whole contact cells are replaced with non-dialable `DEMO-CONTACT-....` tokens; missing contacts remain null. The source has **260 registrations without a phone** and **11 contacts linked to more than one provisional name group**. Shared phones do not trigger automatic person merges. Country codes and lost numeric-cell leading zeros are not guessed. These tokens are suitable for dummy account associations, not real phone authentication or SMS.

No original person names, original phone values, remarks, receipt details or identity mapping were exported. A post-build scan against the private workbook found no source names or phone identifiers in the generated JSON. The source files remain unchanged outside the repository. The retained row references, exact amounts and participation patterns make the history **pseudonymized source-derived data**, not a guarantee of irreversible anonymity. Handle that layer as controlled supervisor-review data. The controlled synthetic cases use independent new IDs and sampled aggregate activity frequencies.

## Activeness: the explicitly approved synthetic override

For a provisional name group `p`, the user-approved synthetic value is:

`event_activeness_score(p) = sum of registrations linked to p across the supplied 2021–2026 history`.

The summary CSV is reconciled on that same grouping and year basis. The resulting full-history registration-frequency scores range from **1 to 6**. Same-year repeats count as registrations in this total. Distinct event-year totals and duplicate flags are preserved separately; registrations do not prove actual physical attendance.

Per the user's instruction, each generated solver participant receives:

```json
{
  "events_joined_last_2_years": 6
}
```

Here `6` is a full-history synthetic proxy, **not an observed two-year count**. The solver contract has an integer input with this field name; there is no independent time-window parameter that transforms the supplied number. Its name and production code remain unchanged. `manifest.json` records this explicit experimental override. Actual prior-two-year distinct event counts and registration counts remain in `history/` and exclude the target year and all future years. For 2021/2022, unavailable pre-2021 history is marked as unobserved rather than claimed absent.

Using all six years for a 2021-labelled synthetic cohort deliberately includes later records. These requests are cross-sectional synthetic cases borrowing the yearly cohort sizes, not historical backtests or predictions. Do not claim there is no future-information leakage in a retrospective experiment using them. A real two-year production implementation should consume the actual lookback counts or formally version/rename the field if the business rule changes.

The solver still normalizes importance within each contribution tier. Different raw scores do not guarantee different seats when hard rules, ties or incomplete optimization dominate. Score ranges alone are not evidence of superior seating quality.

## Contribution checks and missing attributes

Mappings are 梁皇功德主 → `EMPEROR` / RM5,000 minimum; 福慧功德主 → `MERIT` / RM3,000 minimum; 菩提功德主 → `BODHI` / RM2,000 minimum.

The original **2022 sheet, row 82** has a Merit label and **RM1,000**. The masked historical record preserves RM1,000. Following the user's explicit decision, its **synthetic** contribution is RM3,000, with a correction flag; the yearly request retains all 103 registrations. This does not amend the source or establish what the real payment should have been.

The source provides no age, solver role/category, accessibility need, paid-status verification, actual attendance or historical seating layout. Yearly requests use age 40 as a required-schema placeholder, `GENERAL_DEVOTEE`, accessibility false, assumed `CONFIRMED`, no attendance overrides and the existing prototype layout. The prototype demo simulates age and role explicitly. The CSV's loyalty category is not treated as the solver's monastic/committee/volunteer/devotee role.

Except for the discrepancy, observed amounts equal their tier minima. Consequently these yearly cohorts provide little within-tier contribution variation for testing contribution/activity trade-offs. Controlled stress cases deliberately simulate contribution variation and roles to test those factors; those variations are not estimated business facts.

## Controlled case pack and experiment adoption

**Selection decision, 20 October 2026:** the user declined adoption of these 13 controlled candidates and confirmed the separate [benchmark scope amendment](../../../docs/planning/solver-benchmark-scope-amendment-2026-10-20.md) through Q6 A. The benchmark will retain its original generator and activity semantics, adding 179/212-seat occupancy families. This candidate pack, masked history, yearly requests and 2026 demonstration remain available separately; none is an added observation in that benchmark or the unchanged weighting study. The four benchmark prototype timing checks also use benchmark events rather than the demonstration request here. The executable benchmark amendment remains pending. This selection note does not alter generated JSON or historical provenance.

There are 13 controlled cases: mixed/conflict/tied/accessibility at small (24 registrations / 32 seats), typical (96 / 152) and full (152 / 232) sizes, plus one Emperor-heavy mixed case (131 / 230, comprising 99 Emperor, 19 Merit and 13 Bodhi registrations). The heavy case's 75.57% Emperor mix is a declared stress condition, not the sample's typical mix.

Activity is sampled with replacement from the **2026 cohort's tier-conditional full-history frequency distribution**, keeping that calibration cohort explicit. Contribution increments, role/category choices, ages and controlled accessibility assignment are simulated. Conflict cases set contribution inversely to activity; tied cases use tier-minimum contributions. Activity/role/contribution relationships beyond the declared construction are not validated population relationships. Accessibility is assigned only to IDs compatible with a constructive witness, not inferred from age or names.

The existing benchmark command **still generates its original 13 inputs**. It does not automatically load this folder. Before adopting these requests, version the dataset/analysis protocol, record the full-history proxy and case selection, decide whether the six yearly cohorts are a separate empirical-context batch, and run a fresh development pilot under the declared overall budget. Do not append 20 requests to a capped study or combine old/new observations without declaring that change. The weighting experiment remains separate.

## Supervisor review checklist

- Confirm the name-token rule and review flagged variants/namesakes/shared contacts using the private source-row references.
- Confirm all six registration counts, tier mappings and sample coverage, including the 2026 scope.
- Confirm the synthetic RM3,000 exception treatment and assumed seat eligibility.
- Confirm that full-history registration frequency is suitable for the synthetic study, acknowledging its distinction from the live two-year rule and actual attendance.
- Approve or revise simulated roles, ages, contribution variation, accessibility and venue assumptions.
- Approve the selected cases and revised protocol before benchmark adoption. Data preparation and supervisor approval do not prove solver performance or attendee satisfaction.

Validation completed: **six preparation tests passed; 20 requests passed the maintained schema and independent constructive-witness audit; summary reconciliation and source-identifier scan passed**. No optimized seat maps, benchmark measurements or main-study results were generated.
