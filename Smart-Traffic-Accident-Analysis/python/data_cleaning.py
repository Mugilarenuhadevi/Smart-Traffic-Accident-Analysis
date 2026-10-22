"""
data_cleaning.py
----------------
STEP 2 of the pipeline:  raw CSV  ->  cleaned CSV

Input : data/raw/raw_accidents.csv
Output: data/cleaned/cleaned_accidents.csv
        data/cleaned/cleaning_report.txt   (a log of everything that was fixed)

Run:
    python python/data_cleaning.py

Every cleaning decision is explained in a comment starting with "DECISION:".
Those comments are exactly what an interviewer wants to hear you explain.
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = ROOT / "data" / "raw" / "raw_accidents.csv"
CLEAN_FILE = ROOT / "data" / "cleaned" / "cleaned_accidents.csv"
REPORT_FILE = ROOT / "data" / "cleaned" / "cleaning_report.txt"

REPORT = []


def log(msg=""):
    """Print a line AND keep it for the cleaning report file."""
    print(msg)
    REPORT.append(str(msg))


# ----------------------------------------------------------------------------------
# Standardisation dictionaries (lower-case key -> official value)
# ----------------------------------------------------------------------------------
VEHICLE_MAP = {
    "two-wheeler": "Two-Wheeler", "two wheeler": "Two-Wheeler", "2-wheeler": "Two-Wheeler", "bike": "Two-Wheeler",
    "car": "Car", "truck": "Truck", "bus": "Bus", "bicycle": "Bicycle",
    "auto-rickshaw": "Auto-Rickshaw", "auto rickshaw": "Auto-Rickshaw", "auto": "Auto-Rickshaw",
    "rickshaw": "Auto-Rickshaw", "van/lcv": "Van/LCV", "van": "Van/LCV", "lcv": "Van/LCV",
}
WEATHER_MAP = {
    "clear": "Clear", "cloudy": "Cloudy", "light rain": "Light Rain", "drizzle": "Light Rain",
    "heavy rain": "Heavy Rain", "storm": "Heavy Rain", "fog": "Fog",
}
SEVERITY_MAP = {"minor": "Minor", "serious": "Serious", "fatal": "Fatal"}
ALCOHOL_MAP = {"yes": "Yes", "y": "Yes", "no": "No", "n": "No"}
GENDER_MAP = {"male": "Male", "m": "Male", "female": "Female", "f": "Female"}


def standardise(series, mapping, unknown="Unknown"):
    """strip spaces -> lower-case -> map to the official label. Missing/unmapped -> `unknown`."""
    key = series.astype("string").str.strip().str.lower()
    return key.map(mapping).fillna(unknown).astype(object)


def clean_dataframe(df):
    """Full cleaning pipeline. Takes the raw DataFrame, returns the cleaned DataFrame."""
    df = df.copy()

    # ------------------------------------------------------------------ 1. INSPECT
    log("=" * 70)
    log("1. INITIAL INSPECTION")
    log("=" * 70)
    log(f"Shape (rows, columns): {df.shape}")
    log("\nData types:\n" + df.dtypes.to_string())
    missing = df.isna().sum()
    log("\nMissing values per column (only columns with missing data):")
    log(missing[missing > 0].to_string())
    log(f"\nExact duplicate rows: {df.duplicated().sum()}")

    rows_start = len(df)

    # ------------------------------------------------------------------ 2. DUPLICATES
    # DECISION: exact duplicate rows are double data-entry. Keeping them would inflate every
    # count (accidents, casualties...), so we drop them. We keep the FIRST occurrence.
    n_dup = df.duplicated().sum()
    df = df.drop_duplicates().copy()
    # Accident_ID must be unique (it becomes the PRIMARY KEY in MySQL)
    n_dup_id = df.duplicated(subset="Accident_ID").sum()
    df = df.drop_duplicates(subset="Accident_ID").copy()
    log("\n" + "=" * 70)
    log("2. DUPLICATES")
    log("=" * 70)
    log(f"Exact duplicate rows removed : {n_dup}")
    log(f"Duplicate Accident_IDs removed: {n_dup_id}")

    # ------------------------------------------------------------------ 3. TEXT STANDARDISATION
    # DECISION: the same value typed in different ways ("chennai ", "CHENNAI", "Two Wheeler")
    # would be counted as DIFFERENT categories in GROUP BY / Power BI. We map to one label.
    log("\n" + "=" * 70)
    log("3. STANDARDISING CATEGORICAL VALUES")
    log("=" * 70)
    before = {c: df[c].nunique(dropna=True) for c in ["City", "Weather_Condition", "Vehicle_Type",
                                                      "Accident_Severity", "Alcohol_Involved", "Driver_Gender"]}
    df["City"] = df["City"].astype("string").str.strip().str.title().astype(object)
    df["State"] = df["State"].astype("string").str.strip().str.title().astype(object)
    df["Location"] = df["Location"].astype("string").str.strip().astype(object)
    df["Road_Type"] = df["Road_Type"].astype("string").str.strip().str.title().astype(object)
    df["Weather_Condition"] = standardise(df["Weather_Condition"], WEATHER_MAP)
    df["Vehicle_Type"] = standardise(df["Vehicle_Type"], VEHICLE_MAP, unknown="Other")
    df["Accident_Severity"] = standardise(df["Accident_Severity"], SEVERITY_MAP)
    df["Alcohol_Involved"] = standardise(df["Alcohol_Involved"], ALCOHOL_MAP)
    df["Driver_Gender"] = standardise(df["Driver_Gender"], GENDER_MAP)
    for c, n in before.items():
        log(f"{c:<20} unique values: {n:>3} -> {df[c].nunique():>3}")

    # ------------------------------------------------------------------ 4. DATE & TIME
    # DECISION: raw dates arrive in two formats (YYYY-MM-DD and DD/MM/YYYY). We parse each
    # format explicitly (never let pandas guess day/month order) and combine the results.
    log("\n" + "=" * 70)
    log("4. DATE & TIME CONVERSION")
    log("=" * 70)
    d_iso = pd.to_datetime(df["Date"], format="%Y-%m-%d", errors="coerce")
    d_dmy = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")
    df["Date"] = d_iso.fillna(d_dmy)
    n_bad_date = df["Date"].isna().sum()
    log(f"Dates parsed with DD/MM/YYYY fallback: {d_dmy.notna().sum()}")
    log(f"Unparseable dates (rows dropped)     : {n_bad_date}")
    df = df.dropna(subset=["Date"]).copy()

    t = pd.to_datetime(df["Time"], format="%H:%M", errors="coerce")
    df["Hour"] = t.dt.hour
    df["Minute"] = t.dt.minute
    n_bad_time = df["Hour"].isna().sum()
    # DECISION: a row without a usable time cannot be used for hour analysis -> drop (very rare)
    df = df.dropna(subset=["Hour"]).copy()
    log(f"Unparseable times (rows dropped)     : {n_bad_time}")
    df["Hour"] = df["Hour"].astype(int)
    df["Time"] = [f"{h:02d}:{m:02d}:00" for h, m in zip(df["Hour"], df["Minute"].astype(int))]
    df = df.drop(columns="Minute")

    # DECISION: Year / Month / Day_of_Week are RE-DERIVED from the Date column so they can
    # never disagree with it (single source of truth).
    df["Year"] = df["Date"].dt.year
    df["Month_Num"] = df["Date"].dt.month
    df["Month"] = df["Date"].dt.month_name()
    df["Day"] = df["Date"].dt.day
    df["Day_of_Week"] = df["Date"].dt.day_name()
    df["Weekend_Flag"] = (df["Date"].dt.dayofweek >= 5).astype(int)          # 1 = Sat/Sun
    df["Day_Type"] = np.where(df["Weekend_Flag"] == 1, "Weekend", "Weekday")

    # ------------------------------------------------------------------ 5. INVALID VALUES
    log("\n" + "=" * 70)
    log("5. INVALID / IMPOSSIBLE VALUES")
    log("=" * 70)

    # 5a. Driver age -----------------------------------------------------------------
    # DECISION: legal driving age is 18. Ages like 0, -5, 150, 999 are typing errors -> set to
    # missing, then fill with the MEDIAN age of the same vehicle type (median is robust to outliers
    # and a truck driver's typical age differs from a bicycle rider's).
    df["Driver_Age"] = pd.to_numeric(df["Driver_Age"], errors="coerce")
    invalid_age = (df["Driver_Age"] < 18) | (df["Driver_Age"] > 80)
    df.loc[invalid_age, "Driver_Age"] = np.nan
    n_age_missing = df["Driver_Age"].isna().sum()
    df["Driver_Age"] = df["Driver_Age"].fillna(df.groupby("Vehicle_Type")["Driver_Age"].transform("median"))
    df["Driver_Age"] = df["Driver_Age"].fillna(df["Driver_Age"].median()).round().astype(int)
    log(f"Driver_Age: {invalid_age.sum()} invalid values + {n_age_missing - invalid_age.sum()} missing "
        f"-> filled with median age per vehicle type")

    # 5b. Speed limit ----------------------------------------------------------------
    # DECISION: valid speed limits in India are roughly 20-120 km/h. Anything else is an error.
    # Fill with the MODE (most common limit) for the same road type, because the limit is mainly
    # decided by the road type.
    df["Speed_Limit"] = pd.to_numeric(df["Speed_Limit"], errors="coerce")
    invalid_speed = (df["Speed_Limit"] < 20) | (df["Speed_Limit"] > 120)
    df.loc[invalid_speed, "Speed_Limit"] = np.nan
    n_speed_missing = df["Speed_Limit"].isna().sum()
    mode_speed = df.groupby("Road_Type")["Speed_Limit"].agg(lambda s: s.mode().iloc[0])
    df["Speed_Limit"] = df["Speed_Limit"].fillna(df["Road_Type"].map(mode_speed)).astype(int)
    log(f"Speed_Limit: {invalid_speed.sum()} invalid + {n_speed_missing - invalid_speed.sum()} missing "
        f"-> filled with the most common limit for that road type")

    # 5c. Number of vehicles ----------------------------------------------------------
    # DECISION: an accident involves at least 1 vehicle, so 0 is impossible -> set to 1.
    bad_veh = df["Number_of_Vehicles"] < 1
    df.loc[bad_veh, "Number_of_Vehicles"] = 1
    log(f"Number_of_Vehicles: {bad_veh.sum()} zero values corrected to 1")

    # 5d. Fatalities > casualties -----------------------------------------------------
    # DECISION: casualties INCLUDE fatalities, so fatalities can never exceed casualties.
    # A death record is more reliable than a count, so we raise casualties to equal fatalities.
    bad_fat = df["Number_of_Fatalities"] > df["Number_of_Casualties"]
    df.loc[bad_fat, "Number_of_Casualties"] = df.loc[bad_fat, "Number_of_Fatalities"]
    log(f"Fatalities > Casualties: {bad_fat.sum()} rows fixed (casualties raised to match fatalities)")

    # 5e. Severity consistency --------------------------------------------------------
    # DECISION: any accident with a death must be labelled 'Fatal'.
    wrong_sev = (df["Number_of_Fatalities"] > 0) & (df["Accident_Severity"] != "Fatal")
    df.loc[wrong_sev, "Accident_Severity"] = "Fatal"
    log(f"Severity label not 'Fatal' despite deaths: {wrong_sev.sum()} rows fixed")

    # ------------------------------------------------------------------ 6. MISSING VALUES
    log("\n" + "=" * 70)
    log("6. MISSING CATEGORICAL VALUES")
    log("=" * 70)

    # Light_Condition can be DERIVED from the hour of the day -> better than guessing.
    # Daylight/dusk are certain; for night-time we use the most common night label for that road type.
    night_mode = (df[df["Light_Condition"].astype("string").str.startswith("Dark", na=False)]
                  .groupby("Road_Type")["Light_Condition"].agg(lambda s: s.mode().iloc[0]))

    def derive_light(row):
        if 6 <= row["Hour"] <= 17:
            return "Daylight"
        if row["Hour"] in (5, 18, 19):
            return "Dawn/Dusk"
        return night_mode.get(row["Road_Type"], "Darkness - Lights Lit")

    miss_light = df["Light_Condition"].isna()
    df.loc[miss_light, "Light_Condition"] = df[miss_light].apply(derive_light, axis=1)
    log(f"Light_Condition: {miss_light.sum()} missing -> derived from the hour of the day")

    # Road_Condition: if it was raining the road is Wet; otherwise we truly don't know.
    miss_road = df["Road_Condition"].isna()
    rainy = df["Weather_Condition"].isin(["Light Rain", "Heavy Rain"])
    df.loc[miss_road & rainy, "Road_Condition"] = "Wet"
    df["Road_Condition"] = df["Road_Condition"].fillna("Unknown")
    log(f"Road_Condition: {miss_road.sum()} missing -> 'Wet' if raining, otherwise 'Unknown'")

    # DECISION: for Weather, Alcohol and Gender we do NOT guess. Guessing 'No alcohol' would
    # understate alcohol-related accidents. 'Unknown' keeps the row (and its casualties) in the data
    # while staying honest; analysis of alcohol simply excludes 'Unknown'.
    for col in ["Weather_Condition", "Alcohol_Involved", "Driver_Gender"]:
        log(f"{col}: {(df[col] == 'Unknown').sum()} missing -> 'Unknown'")

    # ------------------------------------------------------------------ 7. OUTLIERS
    log("\n" + "=" * 70)
    log("7. OUTLIER CHECK (Number_of_Casualties)")
    log("=" * 70)
    q1, q3 = df["Number_of_Casualties"].quantile([0.25, 0.75])
    upper = q3 + 1.5 * (q3 - q1)
    n_out = (df["Number_of_Casualties"] > upper).sum()
    # DECISION: accidents with many casualties (e.g. a bus crash) are REAL events, not errors.
    # Removing or capping them would hide exactly the most important accidents, so we KEEP them
    # and add a flag column (Mass_Casualty_Flag = 1 when casualties >= 10) for filtering.
    df["Mass_Casualty_Flag"] = (df["Number_of_Casualties"] >= 10).astype(int)
    log(f"IQR upper fence = {upper:.1f}; rows above it = {n_out}")
    log(f"Mass-casualty accidents (>=10 casualties) kept and flagged: {df['Mass_Casualty_Flag'].sum()}")

    # ------------------------------------------------------------------ 8. DERIVED COLUMNS
    log("\n" + "=" * 70)
    log("8. DERIVED COLUMNS")
    log("=" * 70)
    # Casualties per vehicle involved
    df["Casualty_Rate"] = (df["Number_of_Casualties"] / df["Number_of_Vehicles"]).round(2)
    # % of casualties who died (0 when nobody was hurt)
    df["Fatality_Rate"] = np.where(df["Number_of_Casualties"] > 0,
                                   df["Number_of_Fatalities"] / df["Number_of_Casualties"].replace(0, np.nan) * 100,
                                   0).round(2)
    df["Age_Group"] = pd.cut(df["Driver_Age"], bins=[17, 24, 34, 49, 64, 120],
                             labels=["18-24", "25-34", "35-49", "50-64", "65+"]).astype(object)
    df["Time_Period"] = np.select(
        [df["Hour"] <= 4, df["Hour"] <= 7, df["Hour"] <= 10, df["Hour"] <= 15, df["Hour"] <= 20],
        ["Late Night (12-4 AM)", "Early Morning (5-7 AM)", "Morning Peak (8-10 AM)",
         "Midday (11 AM-3 PM)", "Evening Peak (4-8 PM)"],
        default="Night (9-11 PM)")

    # Risk_Category - transparent, rule-based (easy to explain; no ML needed)
    #   Critical : Fatal AND (2+ deaths OR alcohol involved)
    #   High     : any other Fatal accident, OR Serious with 3+ casualties
    #   Medium   : any other Serious accident
    #   Low      : Minor accident
    sev = df["Accident_Severity"]
    df["Risk_Category"] = np.select(
        [(sev == "Fatal") & ((df["Number_of_Fatalities"] >= 2) | (df["Alcohol_Involved"] == "Yes")),
         (sev == "Fatal") | ((sev == "Serious") & (df["Number_of_Casualties"] >= 3)),
         (sev == "Serious")],
        ["Critical", "High", "Medium"], default="Low")
    log("Created: Hour, Day, Month_Num, Weekend_Flag, Day_Type, Time_Period, Casualty_Rate, "
        "Fatality_Rate, Age_Group, Risk_Category, Mass_Casualty_Flag")

    # ------------------------------------------------------------------ 9. FINAL TIDY-UP
    final_cols = ["Accident_ID", "Date", "Time", "Hour", "Day", "Day_of_Week", "Month_Num", "Month", "Year",
                  "Weekend_Flag", "Day_Type", "Time_Period", "Location", "City", "State", "Weather_Condition",
                  "Road_Condition", "Road_Type", "Vehicle_Type", "Number_of_Vehicles", "Number_of_Casualties",
                  "Number_of_Fatalities", "Accident_Severity", "Speed_Limit", "Light_Condition",
                  "Alcohol_Involved", "Driver_Age", "Age_Group", "Driver_Gender", "Casualty_Rate",
                  "Fatality_Rate", "Risk_Category", "Mass_Casualty_Flag"]
    df = df[final_cols].sort_values("Accident_ID").reset_index(drop=True)
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

    log("\n" + "=" * 70)
    log("9. SUMMARY")
    log("=" * 70)
    log(f"Rows before: {rows_start:,} | Rows after: {len(df):,} | Rows removed: {rows_start - len(df):,}")
    log(f"Remaining missing values: {int(df.isna().sum().sum())}")
    return df


def main():
    if not RAW_FILE.exists():
        raise SystemExit(f"Raw file not found: {RAW_FILE}\nRun  python python/generate_dataset.py  first.")
    raw = pd.read_csv(RAW_FILE)
    cleaned = clean_dataframe(raw)
    CLEAN_FILE.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(CLEAN_FILE, index=False, lineterminator="\n")   # \n on every OS so MySQL LOAD DATA works
    REPORT_FILE.write_text("\n".join(REPORT), encoding="utf-8")
    log(f"\nSaved cleaned data   -> {CLEAN_FILE}")
    log(f"Saved cleaning report -> {REPORT_FILE}")


if __name__ == "__main__":
    main()
