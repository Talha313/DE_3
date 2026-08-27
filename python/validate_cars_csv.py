#!/usr/bin/env python3
"""
Validate a car-listing CSV with Great Expectations (same style as HMD_Great_Expectations_2026.py).

Usage:
  python validate_cars_csv.py ../data_smoke/clean\\ synthetic\\ dataset.csv --out ../gx_reports/clean_run
  python validate_cars_csv.py "corrupted synthetic dataset.csv" --out run_corrupt

Expects columns like: listing_id, year, engine_cc, mileage_km, transmission, fuel_type, body_type, city
(Adjust EXPECT_* below if your PakWheels export uses other names.)

Outputs: <out>_suite_result.json, <out>_expectation_summary.csv
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

import great_expectations as gx


def gx_to_dict(result: Any) -> dict:
    if isinstance(result, dict):
        return result
    for name in ("to_json_dict", "as_dict", "model_dump"):
        m = getattr(result, name, None)
        if callable(m):
            try:
                d = m()
                if isinstance(d, dict):
                    return d
            except Exception:
                pass
    try:
        return dict(result)
    except Exception:
        return {"repr": repr(result)}


def build_batch(df: pd.DataFrame):
    context = gx.get_context()
    ds = context.data_sources.add_pandas(name="cars_pandas")
    asset = ds.add_dataframe_asset(name="cars_asset")
    bdef = asset.add_batch_definition_whole_dataframe("whole_df")
    batch = bdef.get_batch(batch_parameters={"dataframe": df})
    return context, bdef, batch


def car_expectations() -> list:
    """Adjust value_set lists after EDA on PakWheels."""
    trans = ["Manual", "Automatic", "manual", "automatic"]
    fuel = ["Petrol", "Diesel", "Hybrid", "petrol", "diesel", "hybrid", "CNG"]
    body = ["Sedan", "SUV", "Hatchback", "Coupe", "Crossover", "Van", "Pickup"]
    city = ["Lahore", "Karachi", "Islamabad", "Rawalpindi", "Faisalabad", "Peshawar", "Multan"]

    ex: list = [
        gx.expectations.ExpectColumnToExist(column="year"),
        gx.expectations.ExpectColumnToExist(column="engine_cc"),
        gx.expectations.ExpectColumnToExist(column="mileage_km"),
        gx.expectations.ExpectColumnToExist(column="transmission"),
        gx.expectations.ExpectColumnToExist(column="fuel_type"),
        gx.expectations.ExpectColumnToExist(column="body_type"),
        gx.expectations.ExpectColumnToExist(column="city"),
        gx.expectations.ExpectColumnValuesToBeBetween(column="year", min_value=1990, max_value=2026),
        gx.expectations.ExpectColumnValuesToBeBetween(column="engine_cc", min_value=600, max_value=8000),
        gx.expectations.ExpectColumnValuesToBeBetween(column="mileage_km", min_value=0, max_value=1_500_000),
        gx.expectations.ExpectColumnValuesToBeInSet(column="transmission", value_set=trans),
        gx.expectations.ExpectColumnValuesToBeInSet(column="fuel_type", value_set=fuel),
        gx.expectations.ExpectColumnValuesToBeInSet(column="body_type", value_set=body),
        gx.expectations.ExpectColumnValuesToBeInSet(column="city", value_set=city),
    ]
    return ex


def car_expectations_with_uniqueness(df: pd.DataFrame) -> list:
    ex = car_expectations()
    if "listing_id" in df.columns:
        ex.append(
            gx.expectations.ExpectColumnValuesToBeUnique(column="listing_id"),
        )
    ex.append(
        gx.expectations.ExpectColumnValuesToNotBeNull(column="mileage_km", mostly=0.95),
    )
    return ex


def summarize_row(result_dict: dict) -> dict:
    cfg = result_dict.get("expectation_config", {})
    res = result_dict.get("result", {})
    return {
        "expectation_type": cfg.get("type") or cfg.get("expectation_type", "unknown"),
        "success": result_dict.get("success"),
        "unexpected_count": res.get("unexpected_count"),
        "unexpected_percent": res.get("unexpected_percent"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path", type=Path)
    ap.add_argument("--out", type=Path, default=Path("gx_validation_out"))
    args = ap.parse_args()

    df = pd.read_csv(args.csv_path)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # map common aliases
    aliases = {
        "engine": "engine_cc",
        "mileage": "mileage_km",
        "fuel": "fuel_type",
    }
    for a, b in aliases.items():
        if a in df.columns and b not in df.columns:
            df.rename(columns={a: b}, inplace=True)

    for c in ["year", "engine_cc", "mileage_km"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    context, bdef, batch = build_batch(df)
    expectations = car_expectations_with_uniqueness(df)

    summaries = []
    raw_results = []
    for exp in expectations:
        r = batch.validate(exp)
        rd = gx_to_dict(r)
        raw_results.append(rd)
        subs = rd.get("results")
        if isinstance(subs, list) and subs:
            for sub in subs:
                summaries.append(summarize_row(sub))
        else:
            summaries.append(summarize_row(rd))

    summ_df = pd.DataFrame(summaries)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    summ_path = args.out.parent / (args.out.name + "_expectation_summary.csv")
    summ_df.to_csv(summ_path, index=False)

    out_json = args.out.parent / (args.out.name + "_suite_result.json")
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(raw_results, f, indent=2, default=str)

    # Optional full suite (GX API varies by version; skip if it errors)
    try:
        suite = gx.ExpectationSuite(name="cars_suite")
        suite = context.suites.add(suite)
        for e in expectations:
            suite.add_expectation(e)
        vd = context.validation_definitions.add(
            gx.core.validation_definition.ValidationDefinition(
                name="cars_validation",
                data=bdef,
                suite=suite,
            )
        )
        suite_result = vd.run(batch_parameters={"dataframe": df})
        suite_json = args.out.parent / (args.out.name + "_full_suite.json")
        with suite_json.open("w", encoding="utf-8") as f:
            json.dump(gx_to_dict(suite_result), f, indent=2, default=str)
        print("Wrote:", suite_json)
    except Exception as e:
        print("Suite export skipped:", e)

    ok = bool(summ_df["success"].all()) if len(summ_df) else True
    print("Wrote:", out_json)
    print("Wrote:", summ_path)
    print(summ_df.to_string())
    print("All expectations success:", ok)


if __name__ == "__main__":
    main()
