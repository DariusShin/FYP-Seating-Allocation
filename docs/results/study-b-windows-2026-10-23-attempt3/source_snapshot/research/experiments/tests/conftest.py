import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "services/seating/src"))
os.environ["SEAT_SOLVER_ROOT"] = str(ROOT)
os.environ["SEAT_SOLVER_RESOURCES"] = str(ROOT / "services/seating")
