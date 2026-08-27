#!/usr/bin/env python3
"""Run every automated check that does not need your secrets or Postgres."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = Path(__file__).resolve().parent


def run(cmd: list[str], cwd: Path | None = None) -> bool:
    print("\n>>>", " ".join(cmd))
    r = subprocess.run(cmd, cwd=cwd or ROOT)
    if r.returncode != 0:
        print(f"   (exit code {r.returncode})")
    return r.returncode == 0


def mod_installed(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def main() -> None:
    print("=== DE Assignment 3 — automated smoke checks ===\n")

    if mod_installed("pandas"):
        print("OK: pandas")
    else:
        print("SKIP/FAIL: pip install pandas")

    if mod_installed("great_expectations"):
        import great_expectations as gx

        print(f"OK: great_expectations {gx.__version__}")
    else:
        print("WARN: great_expectations not installed (needed for Tasks 2–3)")

    if mod_installed("fastapi") and mod_installed("uvicorn"):
        print("OK: fastapi + uvicorn importable")
    else:
        print("WARN: pip install fastapi uvicorn (Part 2)")

    smoke = ROOT / "data_smoke"
    clean_name = "clean synthetic dataset.csv"
    if not (ROOT / clean_name).is_file() and not (smoke / clean_name).is_file():
        print("\n--- Generating minimal smoke CSVs (optional) ---")
        if not run([sys.executable, str(PY / "generate_minimal_synthetic_csvs.py"), "--out", str(smoke)]):
            print("WARN: smoke CSV generation failed")

    check_dir = smoke if (smoke / clean_name).is_file() else ROOT
    print("\n--- Task 1 CSV check ---")
    if not (check_dir / clean_name).is_file():
        print(f"SKIP: no '{clean_name}' in {check_dir} — run PostgreSQL export or generate_minimal_synthetic_csvs.py")
    else:
        run(
            [
                sys.executable,
                str(PY / "verify_task1_csvs.py"),
                "--dir",
                str(check_dir),
            ]
        )

    print("\n--- Course GX tutorial (orders demo) ---")
    tutorial = ROOT / "HMD_Great_Expectations_2026.py"
    if tutorial.is_file() and mod_installed("great_expectations"):
        run([sys.executable, str(tutorial)], cwd=ROOT)
    else:
        print("SKIP: tutorial script or GX missing")

    print("\n--- Part 2 API (only if uvicorn is already running in another terminal) ---")
    print("Train: cd python && python train_pakwheels_svm.py --csv ../data_smoke/\"clean synthetic dataset.csv\" --smoke-label-from mileage_km")
    print("Start: cd python && uvicorn api:app --port 8000")
    print("Then:  python verify_part2_api.py")

    print("\nDone.")


if __name__ == "__main__":
    main()
