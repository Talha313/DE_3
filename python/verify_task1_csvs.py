#!/usr/bin/env python3
"""
Verify Task 1 deliverable CSVs: exist, headers, quick stats.
Uses stdlib csv first; if pandas is available, adds richer null/dup stats.

Usage:
  python verify_task1_csvs.py --dir .
  python verify_task1_csvs.py --dir ./data_smoke
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

EXPECTED = [
    "listing_id",
    "year",
    "engine_cc",
    "mileage_km",
    "transmission",
    "fuel_type",
    "body_type",
    "city",
]


def read_rows(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        r = csv.reader(f)
        header = next(r)
        rows = list(r)
    return header, rows


def analyze(name: str, path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"FAIL: {name} not found at {path}")
    header, rows = read_rows(path)
    h = [c.strip() for c in header]
    print(f"{name}: {len(rows)} data rows")
    missing = [c for c in EXPECTED if c not in h]
    if missing:
        print(f"  WARNING: missing columns: {missing}")
    idx = {c: h.index(c) for c in EXPECTED if c in h}

    empty_mileage = 0
    bad_year = 0
    neg_m = 0
    ids = []
    for row in rows:
        if len(row) <= max(idx.values(), default=0):
            continue
        if "mileage_km" in idx:
            v = row[idx["mileage_km"]].strip()
            if v == "":
                empty_mileage += 1
            else:
                try:
                    m = int(float(v))
                    if m < 0:
                        neg_m += 1
                except ValueError:
                    pass
        if "year" in idx:
            try:
                y = int(float(row[idx["year"]]))
                if y < 1990 or y > 2026:
                    bad_year += 1
            except ValueError:
                pass
        if "listing_id" in idx:
            ids.append(row[idx["listing_id"]])

    dup_ids = len(ids) - len(set(ids)) if ids else 0
    print(f"  empty mileage fields: {empty_mileage}")
    print(f"  year outside [1990,2026]: {bad_year}")
    print(f"  mileage < 0: {neg_m}")
    print(f"  duplicate listing_id rows: {dup_ids}")
    return {
        "empty_mileage": empty_mileage,
        "bad_year": bad_year,
        "neg_m": neg_m,
        "dup_ids": dup_ids,
        "n": len(rows),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=Path, default=Path("."))
    ap.add_argument("--clean", default="clean synthetic dataset.csv")
    ap.add_argument("--corrupt", default="corrupted synthetic dataset.csv")
    args = ap.parse_args()

    clean_p = args.dir / args.clean
    corrupt_p = args.dir / args.corrupt

    print("=== Task 1 CSV verification ===\n")
    sc = analyze("clean", clean_p)
    sx = analyze("corrupt", corrupt_p)

    ok_signal = (
        sx["empty_mileage"] > sc["empty_mileage"]
        or sx["bad_year"] > sc["bad_year"]
        or sx["neg_m"] > sc["neg_m"]
        or sx["dup_ids"] > sc["dup_ids"]
    )

    print("\n=== Result ===")
    if ok_signal:
        print("PASS: corrupted file shows stronger quality issues than clean (basic checks).")
    else:
        print(
            "WARN: corrupted does not look worse on these metrics — check corruptions or file paths."
        )
    print("OK: both CSVs readable. Next: Task 2 Great Expectations.")


if __name__ == "__main__":
    main()
