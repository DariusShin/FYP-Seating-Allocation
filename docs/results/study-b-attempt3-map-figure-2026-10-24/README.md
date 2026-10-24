# Study B attempt 3: heavy-mixed seat-map figure (derived)

Figure B4 shows the CP-SAT and SCIP maps for `heavy-mixed/current`, execution 1 of the primary 60-second, eight-worker cohort. It was rendered from saved records only; no solver was run. [`manifest.json`](manifest.json) records the SHA-256 of the input, run records, both candidates and every exported file.

Both maps were re-checked before rendering for complete coverage of the 131 registration units, 230 distinct seats, entitlement, blocked seats, accessibility and approved Emperor pairs, and their penalties were recomputed from the saved components. Both are proven optimal at 205,150 (production scale), but 65 of 131 registration units hold different seats, and the contribution/activity/category penalties are 2,266/2,025/2,688 for CP-SAT and 2,263/2,021/2,700 for SCIP.

Regenerate into a fresh folder from the repository root:

```powershell
.\.venv-study-b\Scripts\python.exe research/experiments/study_b_map_figure.py --source docs/results/study-b-windows-2026-10-23-attempt3 --out docs/results/<new-folder>
```

Exports: [PDF](figures/b4-heavy-mixed-60s-maps.pdf) · [SVG](figures/b4-heavy-mixed-60s-maps.svg) · [PNG](figures/b4-heavy-mixed-60s-maps.png)
