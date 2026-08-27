-- Synthetic used-car data for AI 620 Assignment 3 (Task 1).
-- Adapt schema/column names to match your lecture notes and GX suites.
-- Run sections manually; fix COPY paths for your OS (or use \copy from psql as normal user).

CREATE EXTENSION IF NOT EXISTS pgcrypto;

DROP TABLE IF EXISTS used_cars_clean CASCADE;
CREATE TABLE used_cars_clean (
    listing_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    year            INTEGER NOT NULL,
    engine_cc       INTEGER NOT NULL,
    mileage_km      INTEGER NOT NULL,
    transmission    TEXT NOT NULL,
    fuel_type       TEXT NOT NULL,
    body_type       TEXT NOT NULL,
    city            TEXT NOT NULL
);

-- Example: 50k rows — increase generate_series upper bound for "larger" data.
INSERT INTO used_cars_clean (year, engine_cc, mileage_km, transmission, fuel_type, body_type, city)
SELECT
    1995 + (random() * 28)::INT AS year,
    (ARRAY[800, 1000, 1300, 1500, 1600, 1800, 2000, 2500])[1 + floor(random() * 8)::INT] AS engine_cc,
    (random() * 350000)::INT AS mileage_km,
    (ARRAY['Manual', 'Automatic'])[1 + floor(random() * 2)::INT],
    (ARRAY['Petrol', 'Diesel', 'Hybrid'])[1 + floor(random() * 3)::INT],
    (ARRAY['Sedan', 'SUV', 'Hatchback', 'Coupe'])[1 + floor(random() * 4)::INT],
    (ARRAY['Lahore', 'Karachi', 'Islamabad', 'Rawalpindi', 'Faisalabad'])[1 + floor(random() * 5)::INT]
FROM generate_series(1, 50000) AS s(i);

-- Export clean CSV (server-side path — must be writable by postgres, or use \copy below)
-- COPY used_cars_clean TO '/tmp/clean synthetic dataset.csv' WITH (FORMAT csv, HEADER true);

-- \copy (SELECT listing_id, year, engine_cc, mileage_km, transmission, fuel_type, body_type, city FROM used_cars_clean)
--   TO 'clean synthetic dataset.csv' CSV HEADER;

-- Corrupted copy: clone then damage (run after clean table is populated)
-- AS SELECT carries data; no PK on new table unless you add one — allows duplicate rows later
DROP TABLE IF EXISTS used_cars_corrupted CASCADE;
CREATE TABLE used_cars_corrupted AS SELECT * FROM used_cars_clean;

-- NULLs in mileage (~5%)
UPDATE used_cars_corrupted
SET mileage_km = NULL
WHERE random() < 0.05;

-- Impossible / out-of-range values
UPDATE used_cars_corrupted SET year = 2035 WHERE random() < 0.01;
UPDATE used_cars_corrupted SET mileage_km = -5000 WHERE random() < 0.005;
UPDATE used_cars_corrupted SET engine_cc = 50 WHERE random() < 0.005;

-- Invalid / inconsistent categoricals
UPDATE used_cars_corrupted SET transmission = 'manul' WHERE random() < 0.01;
UPDATE used_cars_corrupted SET fuel_type = 'PETROLIUM' WHERE random() < 0.01;

-- Duplicate rows (same listing_id appears more than once — breaks uniqueness expectations)
INSERT INTO used_cars_corrupted
SELECT * FROM used_cars_corrupted ORDER BY random() LIMIT 2500;

-- COPY used_cars_corrupted TO '/tmp/corrupted synthetic dataset.csv' WITH (FORMAT csv, HEADER true);

-- From psql (client paths), examples:
-- \copy used_cars_clean (listing_id, year, engine_cc, mileage_km, transmission, fuel_type, body_type, city) TO 'clean synthetic dataset.csv' CSV HEADER
-- \copy used_cars_corrupted (listing_id, year, engine_cc, mileage_km, transmission, fuel_type, body_type, city) TO 'corrupted synthetic dataset.csv' CSV HEADER
