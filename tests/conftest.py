"""Production test configuration.

Production v4 tests build their own requests from the shared synthetic fixture
in research/fixtures; the repository root must be importable for that. The
historical prototype fixtures live with the relocated baseline under
research/baselines/legacy_cp_sat/tests/.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
