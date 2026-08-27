#!/usr/bin/env python3
"""
Cleaning pipeline for Task 4 (synthetic corrupted or similar schema).

Usage:
  python clean_cars.py --in "../corrupted synthetic dataset.csv" --out "../cleaned synthetic dataset.csv"

Change paths or column handling if the file layout differs.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", type=Path, required=True)
    ap.add_argument("--out", dest="out", type=Path, required=True)
    args = ap.parse_args()

    df = pd.read_csv(args.inp)
    df.columns = [c.strip() for c in df.columns]
    n0 = len(df)

    for col in df.select_dtypes(include="object").columns:
        if col == "listing_id":
            df[col] = df[col].astype(str).str.strip()
        else:
            df[col] = df[col].astype(str).str.strip().str.title()

    tx = {"Manul": "Manual", "Manual": "Manual", "Automatic": "Automatic"}
    if "transmission" in df.columns:
        df["transmission"] = df["transmission"].replace(tx)

    fuel_map = {"Petrolium": "Petrol", "PETROLIUM": "Petrol", "Diesel": "Diesel", "Petrol": "Petrol"}
    if "fuel_type" in df.columns:
        df["fuel_type"] = df["fuel_type"].replace(fuel_map)

    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").clip(1990, 2026)

    if "mileage_km" in df.columns:
        df["mileage_km"] = pd.to_numeric(df["mileage_km"], errors="coerce")
        df.loc[df["mileage_km"] < 0, "mileage_km"] = pd.NA
        med = df["mileage_km"].median()
        df["mileage_km"] = df["mileage_km"].fillna(med)

    if "engine_cc" in df.columns:
        df["engine_cc"] = pd.to_numeric(df["engine_cc"], errors="coerce")
        df.loc[df["engine_cc"] < 600, "engine_cc"] = pd.NA
        df["engine_cc"] = df["engine_cc"].fillna(df["engine_cc"].median())

    if "listing_id" in df.columns:
        df = df.drop_duplicates(subset=["listing_id"], keep="first")

    df.to_csv(args.out, index=False)
    print(f"rows {n0} -> {len(df)}")
    print("wrote", args.out.resolve())


if __name__ == "__main__":
    main()
