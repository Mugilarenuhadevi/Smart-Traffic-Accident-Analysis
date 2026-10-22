"""
load_to_mysql.py
----------------
STEP 4 (easy way): load data/cleaned/cleaned_accidents.csv into MySQL.

It creates the database + table (same design as sql/accident_analysis.sql, PART 1) and inserts
all rows. Use this instead of LOAD DATA INFILE if you hit local_infile / secure_file_priv errors.

Install once:   pip install sqlalchemy pymysql
Run:
    python python/load_to_mysql.py --user root --password YOUR_PASSWORD
Optional:  --host localhost --port 3306 --database traffic_accident_db
"""

import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "data" / "cleaned" / "cleaned_accidents.csv"

DDL = """
CREATE TABLE accidents (
    Accident_ID VARCHAR(12) NOT NULL, Accident_Date DATE NOT NULL, Accident_Time TIME NOT NULL,
    Hour TINYINT NOT NULL, Day TINYINT NOT NULL, Day_of_Week VARCHAR(10) NOT NULL,
    Month_Num TINYINT NOT NULL, Month VARCHAR(10) NOT NULL, Year SMALLINT NOT NULL,
    Weekend_Flag TINYINT NOT NULL, Day_Type VARCHAR(8) NOT NULL, Time_Period VARCHAR(30) NOT NULL,
    Location VARCHAR(60) NOT NULL, City VARCHAR(30) NOT NULL, State VARCHAR(30) NOT NULL,
    Weather_Condition VARCHAR(20) NOT NULL, Road_Condition VARCHAR(25) NOT NULL,
    Road_Type VARCHAR(20) NOT NULL, Vehicle_Type VARCHAR(20) NOT NULL,
    Number_of_Vehicles TINYINT NOT NULL, Number_of_Casualties SMALLINT NOT NULL,
    Number_of_Fatalities SMALLINT NOT NULL, Accident_Severity VARCHAR(10) NOT NULL,
    Speed_Limit SMALLINT NOT NULL, Light_Condition VARCHAR(30) NOT NULL,
    Alcohol_Involved VARCHAR(10) NOT NULL, Driver_Age TINYINT UNSIGNED NOT NULL,
    Age_Group VARCHAR(10) NOT NULL, Driver_Gender VARCHAR(10) NOT NULL,
    Casualty_Rate DECIMAL(6,2) NOT NULL, Fatality_Rate DECIMAL(6,2) NOT NULL,
    Risk_Category VARCHAR(10) NOT NULL, Mass_Casualty_Flag TINYINT NOT NULL,
    PRIMARY KEY (Accident_ID),
    INDEX idx_year (Year), INDEX idx_city (City), INDEX idx_location (Location),
    INDEX idx_severity (Accident_Severity), INDEX idx_hour (Hour)
) ENGINE = InnoDB
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", default=3306, type=int)
    ap.add_argument("--user", default="root")
    ap.add_argument("--password", default="")
    ap.add_argument("--database", default="traffic_accident_db")
    a = ap.parse_args()

    if not CSV.exists():
        raise SystemExit(f"{CSV} not found. Run python python/data_cleaning.py first.")

    df = pd.read_csv(CSV).rename(columns={"Date": "Accident_Date", "Time": "Accident_Time"})

    server = create_engine(f"mysql+pymysql://{a.user}:{a.password}@{a.host}:{a.port}/")
    with server.begin() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {a.database} CHARACTER SET utf8mb4"))

    engine = create_engine(f"mysql+pymysql://{a.user}:{a.password}@{a.host}:{a.port}/{a.database}")
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS accidents"))
        conn.execute(text(DDL))
    df.to_sql("accidents", engine, if_exists="append", index=False, chunksize=2000)

    with engine.connect() as conn:
        n = conn.execute(text("SELECT COUNT(*) FROM accidents")).scalar()
    print(f"Loaded {n:,} rows into {a.database}.accidents")


if __name__ == "__main__":
    main()
