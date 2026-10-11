# Relocation note for the 2026-10-11 preference sensitivity bundle

This bundle was recorded on 11 October 2026 from the repository paths listed in
`manifest.json`. It was later relocated unchanged as part of the repository
restructuring described in `docs/planning/repository-restructuring.md`.

## Path map

| Original path at recording time | Current location |
|---|---|
| `experiments/results/preference-sensitivity-2026-10-11/` (this bundle) | `docs/results/preference-sensitivity-2026-10-11/` |
| `experiments/preference_sensitivity.py` | `research/experiments/preference_sensitivity.py` |
| `config/production_policy.json` | unchanged |
| `src/seat_solver/production/*.py` | unchanged at recording time |

## Integrity and provenance

- Every recorded file in this bundle is preserved byte-for-byte; `manifest.json`,
  `summary.json`, `results.md`, `proof_comparisons.json`, `inputs/` and `runs/`
  are not edited to reflect the new paths.
- `manifest.json` records 15 `source_sha256` entries with their original
  repository-relative paths. Those paths are historical recording-time paths and
  are intentionally not rewritten.
- `source_snapshot/experiments/preference_sensitivity.py` is a byte-for-byte
  copy of the untracked runner as it existed when the study was recorded
  (SHA-256 `a51829f11b814fafeeaa5baee2a79835c7909ff1454e9418ab11f740e0aec81f`,
  matching `manifest.json`). The remaining 14 hashed sources were tracked and
  unmodified at recording time and remain recoverable from Git history.
- The relocated runner under `research/experiments/` may receive later
  maintenance changes; the snapshot, not the maintained copy, is the
  provenance reference for this study.
- Any reproduction check must run into a fresh output directory and compare
  against this bundle, accounting for machine, dependency and time-budget
  differences.
