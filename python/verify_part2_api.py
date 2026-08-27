#!/usr/bin/env python3
"""
Test FastAPI after: uvicorn api:app --reload --port 8000
Usage:
  python verify_part2_api.py
  python verify_part2_api.py --base http://127.0.0.1:8000
"""

from __future__ import annotations

import argparse
import json
import sys

try:
    import requests
except ImportError:
    print("pip install requests", file=sys.stderr)
    raise

PAYLOAD = {
    "year": 2018,
    "engine": 1300,
    "mileage": 45000,
    "transmission": "Manual",
    "fuel": "Petrol",
    "body_type": "Sedan",
    "city": "Lahore",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8000")
    args = ap.parse_args()
    base = args.base.rstrip("/")

    print("GET /health")
    try:
        r = requests.get(f"{base}/health", timeout=5)
        r.raise_for_status()
        print(json.dumps(r.json(), indent=2))
    except requests.RequestException as e:
        raise SystemExit(f"FAIL: is uvicorn running? {e}") from e

    print("\nPOST /predict")
    try:
        r = requests.post(f"{base}/predict", json=PAYLOAD, timeout=10)
        print("status:", r.status_code)
        print(r.text)
        r.raise_for_status()
    except requests.RequestException as e:
        raise SystemExit(
            f"FAIL: {e}\n"
            "Common fixes: train with train_pakwheels_svm.py, put .pkl in cwd or set MODEL_PATH; "
            "API field names must match training columns."
        ) from e

    print("\nPASS: API responded. Next: streamlit run frontend.py")


if __name__ == "__main__":
    main()
