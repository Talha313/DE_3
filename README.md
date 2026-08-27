# AI 620 — Assignment 3

| Item | Role |
|------|------|
| `sql/01_generate_synthetic_cars.sql` | PostgreSQL → `clean synthetic dataset.csv` / corrupted table (then `\copy`). |
| `data_smoke/` | Tiny CSV pair to test GX/cleaning without Postgres (not a substitute for Task 1). |
| `python/validate_cars_csv.py` | Great Expectations on any car-style CSV; writes JSON + CSV summary. |
| `python/clean_cars.py` | Cleans corrupted synthetic-style CSV → `cleaned synthetic dataset.csv`. |
| `python/train_pakwheels_svm.py` | Trains `Pipeline` + SVM; saves **`pakwheels_svm_model.pkl`** (LMS PakWheels CSV + target column). |
| `python/api.py` | FastAPI `POST /predict` (loads the pickle pipeline). |
| `python/frontend.py` | Streamlit UI calling the API. |
| `HMD_Great_Expectations_2026.py` | Course tutorial — run first if GX install is new. |


