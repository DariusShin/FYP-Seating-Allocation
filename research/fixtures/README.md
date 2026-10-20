# Research input fixtures

`synthetic_participants.py` is the existing random request generator used by production tests and the original benchmark. Its inputs and the frozen benchmark protocol have not been replaced.

The new [PJKIT sample-data bundle](pjkit-sample-2026-10-20/README.md) contains masked 2021–2026 registration history, six source-count-matched synthetic cohorts, a prototype demo and 13 independently generated controlled cases. Start with that README and `data-quality.json` before using the data in a dissertation study.

## Reproduce the source-informed dataset

`pjkit_sample_data.py extract` needs Python with **openpyxl 3.1.5**. `build` uses the existing project `.venv` and its solver schema/validator. Keeping extraction dependencies separate avoids changing the locked benchmark environment. The supplied workbook and CSV remain private local inputs; do not copy them into Git or add a real-name/phone mapping.

For example, prepare a separate extraction environment if needed:

```sh
python3 -m venv /private/tmp/pjkit-history-env
/private/tmp/pjkit-history-env/bin/python -m pip install openpyxl==3.1.5
```

From the repository root, choose a **new** output directory for another version:

```sh
/private/tmp/pjkit-history-env/bin/python research/fixtures/pjkit_sample_data.py extract \
  --workbook "/Users/dariusleeshin/Downloads/PJKIT Sample Event Data.xlsx" \
  --summary "/Users/dariusleeshin/Downloads/PJKIT Sample Event Data - Summary.csv" \
  --out research/fixtures/pjkit-sample-review-v2

.venv/bin/python research/fixtures/pjkit_sample_data.py build \
  --out research/fixtures/pjkit-sample-review-v2

/private/tmp/pjkit-history-env/bin/python research/fixtures/pjkit_sample_data.py privacy-check \
  --workbook "/Users/dariusleeshin/Downloads/PJKIT Sample Event Data.xlsx" \
  --out research/fixtures/pjkit-sample-review-v2

.venv/bin/python -m pytest research/experiments/tests/test_pjkit_sample_data.py -q
```

The bundled spreadsheet-analysis Python was used for extraction of the delivered bundle, with openpyxl 3.1.5. No additional dependency was installed into the benchmark environment for that extraction. The original workbook and CSV were read without modification.

Extraction verifies the supplied six yearly counts and reconciles the CSV against the workbook after display-name grouping. It replaces names/contact values in memory and writes only masked data. It preserves discrepancies and records the user-approved synthetic amount correction. Building validates all requests against the maintained contract and audits constructive placement witnesses. **Neither step invokes a solver or runs the benchmark.** Re-extraction/build into an already populated destination is refused.

All requests use the existing `events_joined_last_2_years` field but intentionally encode the user-approved **full-history synthetic registration-frequency proxy**. Actual prior-two-year counts remain separate in the history. See the bundle README for the implications and supervisor review checklist.

The [20 October scope amendment](../../docs/planning/solver-benchmark-scope-amendment-2026-10-20.md), confirmed through Q6 A, explicitly excludes the 13 source-informed controlled candidates from benchmark adoption. Keep their files, masked historical/yearly data and separate prototype demo available. The expanded benchmark will retain the original generator/activity semantics and add two four-pattern occupancy families; its executable amendment is pending. The weighting study and original development evidence remain separate. Any later candidate adoption requires its own versioned protocol and fresh pilot.
