#!/usr/bin/env python3
"""
Train SVM + preprocessing, save ONE pickle for FastAPI (Pipeline).

Your LMS CSV must have numeric + categorical columns and a binary target.

Example:
  python train_pakwheels_svm.py --csv ~/pakwheels.csv --target high_price

Smoke test (no target column): derive a fake binary label from a numeric column:
  python train_pakwheels_svm.py --csv ../data_smoke/clean\\ synthetic\\ dataset.csv --smoke-label-from mileage_km

Rename columns in a spreadsheet first if needed to match:
  year, engine_cc, mileage_km, transmission, fuel_type, body_type, city, <target>
"""

from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC

NUMERIC = ["year", "engine_cc", "mileage_km"]
CAT = ["transmission", "fuel_type", "body_type", "city"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, required=True)
    ap.add_argument("--target", type=str, default="high_price")
    ap.add_argument(
        "--smoke-label-from",
        type=str,
        default=None,
        metavar="COL",
        help="If set, build binary y = (COL > median); for local smoke only, not for submission.",
    )
    ap.add_argument("--out", type=Path, default=Path("pakwheels_svm_model.pkl"))
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    if args.smoke_label_from:
        col = args.smoke_label_from.strip().lower().replace(" ", "_")
        if col not in df.columns:
            raise SystemExit(f"--smoke-label-from: missing column {col!r}")
        v = pd.to_numeric(df[col], errors="coerce")
        med = v.median()
        y = (v > med).astype(int)
    elif args.target not in df.columns:
        raise SystemExit(f"Missing target column {args.target!r}. Columns: {list(df.columns)}")
    else:
        y = df[args.target].astype(int)
    use_num = [c for c in NUMERIC if c in df.columns]
    use_cat = [c for c in CAT if c in df.columns]
    if len(use_num) + len(use_cat) < 3:
        raise SystemExit(f"Need more feature columns. Have num={use_num} cat={use_cat}")

    X = df[use_num + use_cat]

    pre = ColumnTransformer(
        [
            ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), use_num),
            (
                "cat",
                Pipeline(
                    [
                        ("imp", SimpleImputer(strategy="most_frequent")),
                        ("oh", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                    ]
                ),
                use_cat,
            ),
        ]
    )

    model = Pipeline([("pre", pre), ("clf", SVC(kernel="rbf", class_weight="balanced"))])
    model.fit(X, y)

    bundle = {"pipeline": model, "numeric_cols": use_num, "categorical_cols": use_cat}
    joblib.dump(bundle, args.out)
    print("saved", args.out.resolve(), "rows=", len(df))


if __name__ == "__main__":
    main()
