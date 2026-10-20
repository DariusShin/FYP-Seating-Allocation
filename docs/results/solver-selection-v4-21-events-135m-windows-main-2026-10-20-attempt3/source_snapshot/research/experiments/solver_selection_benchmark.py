"""CLI for the controlled CP-SAT / SCIP / greedy experiment (see --help)."""

import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "services/seating/src"))
# Never accidentally import an editable installation from a different checkout.
os.environ["SEAT_SOLVER_ROOT"] = str(ROOT)
os.environ["SEAT_SOLVER_RESOURCES"] = str(ROOT / "services/seating")

if __name__ == "__main__":
    from research.experiments.solver_benchmark.runner import main
    raise SystemExit(main())
