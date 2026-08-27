#!/usr/bin/env python3
"""
Optional: tiny clean + corrupted CSVs (same column names as sql/01_generate_synthetic_cars.sql).
For GX / pipeline smoke tests only. Task 1 still requires PostgreSQL per brief.

Usage:
  python generate_minimal_synthetic_csvs.py --out ./data_smoke
"""

from __future__ import annotations

import argparse
import csv
import random
import uuid
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("data_smoke"))
    ap.add_argument("--rows", type=int, default=2000)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    rng = random.Random(42)
    n = args.rows
    cities = ["Lahore", "Karachi", "Islamabad", "Rawalpindi", "Faisalabad"]
    bodies = ["Sedan", "SUV", "Hatchback", "Coupe"]
    trans = ["Manual", "Automatic"]
    fuels = ["Petrol", "Diesel", "Hybrid"]
    engines = [800, 1000, 1300, 1500, 1800, 2000]

    cols = [
        "listing_id",
        "year",
        "engine_cc",
        "mileage_km",
        "transmission",
        "fuel_type",
        "body_type",
        "city",
    ]

    def row():
        return [
            str(uuid.uuid4()),
            rng.randint(1998, 2024),
            rng.choice(engines),
            rng.randint(0, 350_000),
            rng.choice(trans),
            rng.choice(fuels),
            rng.choice(bodies),
            rng.choice(cities),
        ]

    clean_path = args.out / "clean synthetic dataset.csv"
    rows = [row() for _ in range(n)]
    with clean_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(rows)

    corrupt_path = args.out / "corrupted synthetic dataset.csv"
    bad = list(rows)
    for i in rng.sample(range(n), k=max(1, n // 20)):
        bad[i] = bad[i].copy()
        bad[i][3] = ""  # null mileage as empty string -> read as NaN in pandas
    for i in rng.sample(range(n), k=max(1, n // 50)):
        bad[i] = list(bad[i])
        bad[i][1] = 2035
    for i in rng.sample(range(n), k=max(1, n // 100)):
        bad[i] = list(bad[i])
        bad[i][3] = -1000
    for i in rng.sample(range(n), k=max(1, n // 80)):
        bad[i] = list(bad[i])
        bad[i][4] = "manul"
    bad.extend(bad[: max(1, n // 40)])

    with corrupt_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in bad:
            w.writerow(r)

    print("Wrote:", clean_path.resolve())
    print("Wrote:", corrupt_path.resolve())


if __name__ == "__main__":
    main()
