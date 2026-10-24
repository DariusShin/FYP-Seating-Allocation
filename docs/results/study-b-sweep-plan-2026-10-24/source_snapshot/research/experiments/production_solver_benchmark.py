"""Windows-ready Study B CLI. Run --help; never imports a different checkout."""

import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "services/seating/src"))
os.environ["SEAT_SOLVER_ROOT"] = str(ROOT)
os.environ["SEAT_SOLVER_RESOURCES"] = str(ROOT / "services/seating")
os.environ["PYTHONUTF8"] = "1"

if __name__ == "__main__":
    from research.experiments.production_benchmark.runner import main
    raise SystemExit(main())
