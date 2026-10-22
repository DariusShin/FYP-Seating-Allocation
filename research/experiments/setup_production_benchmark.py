"""Create an isolated Study B environment on Windows 11 (or for development).

This installs dependencies only. It never starts a pilot or measured experiment.
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--venv", type=Path, default=ROOT / ".venv-study-b")
    args = parser.parse_args()
    if sys.version_info < (3, 12):
        raise SystemExit("Use 64-bit Python 3.12 or newer; Python 3.14 matches the recorded Study A environment")
    if sys.maxsize <= 2**32:
        raise SystemExit("A 64-bit interpreter is required")
    directory = args.venv.resolve()
    marker = directory / ".study-b-environment.json"
    if directory.exists():
        if not marker.exists() or json.loads(marker.read_text(encoding="utf-8")).get("root") != str(ROOT):
            raise SystemExit("Refusing to modify an unowned/existing environment; select a fresh --venv directory")
    else:
        venv.EnvBuilder(with_pip=True).create(directory)
        marker.write_text(json.dumps(dict(root=str(ROOT), purpose="Study B research only"), indent=2) + "\n", encoding="utf-8")
    interpreter = directory / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    subprocess.run([str(interpreter), "-m", "pip", "install", "--disable-pip-version-check", "--no-input",
                    "--cache-dir", str(directory / "pip-cache"), "-r",
                    str(ROOT / "research/experiments/requirements-study-b.txt")], cwd=ROOT, check=True)
    subprocess.run([str(interpreter), "-c", "from ortools.linear_solver import pywraplp; "
                    "s=pywraplp.Solver.CreateSolver('SCIP'); assert s is not None; print(s.SolverVersion()); "
                    "print('Dependency installation complete. Actual native concurrency still requires the preflight.')"], check=True)
    print(f"Study B interpreter: {interpreter}")
    print("Next: research/experiments/run_study_b_windows.ps1 -Mode check -Out docs/results/study-b-check-<date>")


if __name__ == "__main__":
    main()
