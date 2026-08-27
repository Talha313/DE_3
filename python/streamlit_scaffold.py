"""
Part 2 — Streamlit client for FastAPI /predict.
Run API first, then: streamlit run streamlit_scaffold.py

Set API_URL if not localhost.
"""

import os

import requests
import streamlit as st

API_URL = os.environ.get("PAKWHEELS_API_URL", "http://127.0.0.1:8000")


st.set_page_config(page_title="PakWheels price category", layout="centered")
st.title("Used car price category")

with st.form("car"):
    year = st.number_input("Year", min_value=1990, max_value=2026, value=2018)
    engine = st.number_input("Engine (cc)", min_value=600, max_value=5000, value=1300)
    mileage = st.number_input("Mileage (km)", min_value=0, value=45000)
    transmission = st.selectbox("Transmission", ["Manual", "Automatic"])
    fuel = st.selectbox("Fuel", ["Petrol", "Diesel", "Hybrid"])
    body_type = st.text_input("Body type", value="Sedan")
    city = st.text_input("City", value="Lahore")
    submitted = st.form_submit_button("Predict")

if submitted:
    payload = {
        "year": int(year),
        "engine": int(engine),
        "mileage": int(mileage),
        "transmission": transmission,
        "fuel": fuel,
        "body_type": body_type,
        "city": city,
    }
    try:
        r = requests.post(f"{API_URL}/predict", json=payload, timeout=10)
        r.raise_for_status()
        out = r.json()
        st.success(f"Predicted category: **{out.get('price_category', out)}**")
    except requests.RequestException as e:
        st.error(f"API error: {e}. Is uvicorn running on {API_URL}?")
