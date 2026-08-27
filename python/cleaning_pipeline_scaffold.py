"""
Part 1 Task 4 — cleaning pipeline scaffold.
Read corrupted / PakWheels CSV, apply rules, write cleaned CSV, then re-run GX checkpoint.
Implement each step; keep a short log of row counts before/after.
"""

from pathlib import Path

import pandas as pd

# Paths — set to match local CSVs
INPUT_CSV = Path("corrupted synthetic dataset.csv")
OUTPUT_CSV = Path("cleaned_synthetic_dataset.csv")


def main():
    df = pd.read_csv(INPUT_CSV)
    n0 = len(df)

    # Example: strip categoricals
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip().str.title()

    # Example: map common typos (extend from your GX failures)
    transmission_map = {"Manul": "Manual", "MANUAL": "Manual"}
    if "transmission" in df.columns:
        df["transmission"] = df["transmission"].replace(transmission_map)

    # Example: clip year
    if "year" in df.columns:
        df["year"] = df["year"].clip(lower=1990, upper=2026)

    # Example: drop negative mileage; impute nulls with median
    if "mileage_km" in df.columns:
        df.loc[df["mileage_km"] < 0, "mileage_km"] = pd.NA
        med = df["mileage_km"].median()
        df["mileage_km"] = df["mileage_km"].fillna(med)

    # Example: dedupe on listing_id if present
    if "listing_id" in df.columns:
        df = df.drop_duplicates(subset=["listing_id"], keep="first")

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"rows {n0} -> {len(df)} | wrote {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
