"""Create a local research environment without modifying the production environment.

Usage: python3.12-or-newer research/experiments/setup_benchmark.py
"""

from pathlib import Path
import os
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parents[2]


def main():
    if sys.version_info < (3, 12):
        raise SystemExit("Run this setup with Python 3.12 or newer (required by the tested dependency lock)")
    directory = ROOT / ".venv"
    interpreter = directory / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not interpreter.exists():
        venv.EnvBuilder(with_pip=True).create(directory)
    subprocess.run([str(interpreter), "-c", "import sys; "
                    "sys.exit('Existing .venv needs Python 3.12 or newer') if sys.version_info < (3, 12) else None"], check=True)
    subprocess.run([str(interpreter), "-m", "pip", "install", "--cache-dir", str(directory / "pip-cache"),
                    "-r", str(ROOT / "research/experiments/requirements-benchmark-lock.txt")], check=True)
    subprocess.run([str(interpreter), "-c", "from ortools.linear_solver import pywraplp; "
                    "s=pywraplp.Solver.CreateSolver('SCIP'); assert s is not None; print(s.SolverVersion())"], check=True)
    print(f"Ready: {interpreter.relative_to(ROOT)} research/experiments/solver_selection_benchmark.py --help")


if __name__ == "__main__":
    main()
