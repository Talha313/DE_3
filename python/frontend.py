"""Streamlit UI. Set PAKWHEELS_API_URL if API is not localhost."""

from __future__ import annotations

import os

import requests
import streamlit as st

API = os.environ.get("PAKWHEELS_API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="PakWheels price class", layout="centered")
st.title("Used car — high / low price")

with st.form("f"):
    y = st.number_input("Year", 1990, 2026, 2018)
    eng = st.number_input("Engine (cc)", 600, 8000, 1300)
    mil = st.number_input("Mileage (km)", 0, 2_000_000, 45000)
    tr = st.selectbox("Transmission", ["Manual", "Automatic"])
    fu = st.selectbox("Fuel", ["Petrol", "Diesel", "Hybrid"])
    body = st.text_input("Body type", "Sedan")
    city = st.text_input("City", "Lahore")
    go = st.form_submit_button("Predict")

if go:
    payload = {
        "year": int(y),
        "engine": int(eng),
        "mileage": int(mil),
        "transmission": tr,
        "fuel": fu,
        "body_type": body,
        "city": city,
    }
    try:
        r = requests.post(f"{API.rstrip('/')}/predict", json=payload, timeout=15)
        r.raise_for_status()
        j = r.json()
        st.success(f"Category: **{j.get('price_category', j)}** (label={j.get('label')})")
    except Exception as e:
        st.error(f"{e} — start API: uvicorn api:app --port 8000")
