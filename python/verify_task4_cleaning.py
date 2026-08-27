#!/usr/bin/env python3
"""Check cleaning output exists and basic shape vs input. Adjust paths to your files."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    if not args.input.is_file():
        raise SystemExit(f"Input missing: {args.input} — run cleaning first or fix the path.")

    if not args.output.is_file():
        raise SystemExit(
            f"Output missing: {args.output}\n"
            "Run clean_cars.py (or your pipeline) and re-run this check."
        )

    a = pd.read_csv(args.input)
    b = pd.read_csv(args.output)
    print(f"Input rows: {len(a)} | Output rows: {len(b)}")
    if len(b) > len(a):
        print("WARN: output has more rows than input — unusual unless you merged data.")
    if len(b) < len(a):
        print(f"Rows dropped/reduced: {len(a) - len(b)}")
    print("PASS: cleaned file exists and is readable.")


if __name__ == "__main__":
    main()
