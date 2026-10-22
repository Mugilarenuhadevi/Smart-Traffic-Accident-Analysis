"""
generate_dataset.py
-------------------
Creates a realistic SYNTHETIC road-accident dataset (~12,000 rows) for Indian cities
and saves it to  data/raw/raw_accidents.csv

Why synthetic?
    A public dataset would work too (see README -> "Dataset"), but a generated one lets us
    (a) control the size, (b) keep the columns exactly as required and
    (c) deliberately add REAL-WORLD DIRT (missing values, duplicates, typos, invalid values)
    so the cleaning step in data_cleaning.py has something meaningful to fix.

How the realism is built (this is a great interview talking point):
    Severity is NOT random. Every accident gets a hidden "risk score" which goes UP with
    higher speed limits, alcohol, fog / heavy rain, darkness without street lights, damaged
    roads, two-wheelers / trucks, young or elderly drivers, and risky locations.
    Severity (Minor / Serious / Fatal) is then derived from that score + random noise.
    Time-of-day, weekday, month and year patterns are also built in.

Run:
    python python/generate_dataset.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
N_ROWS = 12_000
rng = np.random.default_rng(SEED)

ROOT = Path(__file__).resolve().parents[1]
OUT_FILE = ROOT / "data" / "raw" / "raw_accidents.csv"

# --------------------------------------------------------------------------------------
# 1. LOCATION MASTER TABLE
#    (city, state, city_weight, [(location, road_type, location_risk_factor), ...])
#    risk factor > 1  => more accidents AND more severe accidents at that spot
# --------------------------------------------------------------------------------------
CITIES = [
    ("Chennai", "Tamil Nadu", 1.30, [
        ("Anna Salai Junction", "Urban Road", 1.15), ("GST Road Tambaram", "Highway", 1.45),
        ("OMR Sholinganallur", "Urban Road", 1.20), ("Koyambedu Flyover", "Urban Road", 1.10),
        ("ECR Muttukadu", "Highway", 1.30)]),
    ("Bengaluru", "Karnataka", 1.40, [
        ("Silk Board Junction", "Urban Road", 1.50), ("Hebbal Flyover", "Urban Road", 1.20),
        ("Electronic City Elevated", "Expressway", 1.25), ("Tumkur Road NH48", "Highway", 1.35),
        ("Outer Ring Road Marathahalli", "Urban Road", 1.15)]),
    ("Mumbai", "Maharashtra", 1.45, [
        ("Western Express Highway", "Highway", 1.40), ("Eastern Freeway", "Expressway", 1.20),
        ("Sion-Panvel Road", "Highway", 1.25), ("Bandra-Worli Sea Link", "Expressway", 0.80),
        ("LBS Marg Kurla", "Urban Road", 1.10)]),
    ("Delhi", "Delhi", 1.50, [
        ("Ring Road Ashram", "Urban Road", 1.30), ("NH44 Singhu Border", "Highway", 1.55),
        ("Yamuna Expressway Entry", "Expressway", 1.45), ("Outer Ring Road Rohini", "Urban Road", 1.15),
        ("Mathura Road Badarpur", "Highway", 1.35)]),
    ("Hyderabad", "Telangana", 1.10, [
        ("Outer Ring Road Gachibowli", "Expressway", 1.25), ("Nehru Outer Ring Exit 12", "Expressway", 1.35),
        ("LB Nagar Junction", "Urban Road", 1.15), ("NH65 Patancheru", "Highway", 1.40),
        ("Banjara Hills Road 12", "Urban Road", 0.85)]),
    ("Kolkata", "West Bengal", 0.95, [
        ("EM Bypass Ruby", "Highway", 1.25), ("Howrah Bridge Approach", "Urban Road", 1.15),
        ("Barasat Highway", "Highway", 1.35), ("Park Street Crossing", "Urban Road", 0.85),
        ("VIP Road Airport", "Urban Road", 1.00)]),
    ("Pune", "Maharashtra", 0.95, [
        ("Mumbai-Pune Expressway Khandala", "Expressway", 1.60), ("Katraj Chowk", "Urban Road", 1.20),
        ("Hinjewadi Phase 1", "Urban Road", 1.10), ("Pune-Nashik Highway Moshi", "Highway", 1.30),
        ("Satara Road Bibwewadi", "Highway", 1.20)]),
    ("Ahmedabad", "Gujarat", 0.80, [
        ("SG Highway", "Highway", 1.20), ("Sardar Patel Ring Road", "Expressway", 1.25),
        ("CG Road", "Urban Road", 0.90), ("Naroda Highway", "Highway", 1.30),
        ("Vastral Road", "Urban Road", 1.00)]),
    ("Jaipur", "Rajasthan", 0.75, [
        ("Ajmer Road Sirsi", "Highway", 1.40), ("Tonk Road Durgapura", "Urban Road", 1.10),
        ("Delhi Bypass Chomu", "Highway", 1.45), ("MI Road", "Urban Road", 0.85),
        ("Jaipur-Agra Highway Kukas", "Rural Road", 1.35)]),
    ("Coimbatore", "Tamil Nadu", 0.65, [
        ("Avinashi Road", "Urban Road", 1.15), ("Trichy Road Singanallur", "Highway", 1.25),
        ("Salem-Kochi Highway Madukkarai", "Highway", 1.40), ("Race Course Road", "Urban Road", 0.80),
        ("Pollachi Road Rural Stretch", "Rural Road", 1.30)]),
]
NORTH_FOG_CITIES = {"Delhi", "Jaipur", "Kolkata", "Ahmedabad"}

# Flatten to arrays so we can sample vectorised
loc_rows = []
for city, state, cw, locs in CITIES:
    for loc, rtype, risk in locs:
        loc_rows.append((city, state, loc, rtype, risk, cw * risk))
LOC = pd.DataFrame(loc_rows, columns=["City", "State", "Location", "Road_Type", "Risk", "Weight"])
LOC["Weight"] = LOC["Weight"] / LOC["Weight"].sum()

# --------------------------------------------------------------------------------------
# 2. DATES  (2019-2023)  with year / month / weekday seasonality
# --------------------------------------------------------------------------------------
all_days = pd.date_range("2019-01-01", "2023-12-31", freq="D")
year_w = {2019: 1.00, 2020: 0.72, 2021: 0.90, 2022: 1.05, 2023: 1.12}   # 2020 = COVID lockdown dip
month_w = {1: 1.10, 2: 0.95, 3: 0.95, 4: 0.95, 5: 1.00, 6: 0.95,
           7: 1.00, 8: 1.00, 9: 1.00, 10: 1.10, 11: 1.15, 12: 1.15}      # festive season + fog
dow_w = {0: 0.93, 1: 0.93, 2: 0.95, 3: 1.00, 4: 1.12, 5: 1.15, 6: 1.02}  # Fri / Sat peak
day_weights = np.array([year_w[d.year] * month_w[d.month] * dow_w[d.dayofweek] for d in all_days])
day_weights = day_weights / day_weights.sum()

dates = pd.DatetimeIndex(rng.choice(all_days, size=N_ROWS, p=day_weights))
df = pd.DataFrame({"Date": dates})
df["is_weekend"] = df["Date"].dt.dayofweek >= 5

# --------------------------------------------------------------------------------------
# 3. LOCATION / CITY / STATE / ROAD TYPE
# --------------------------------------------------------------------------------------
loc_idx = rng.choice(len(LOC), size=N_ROWS, p=LOC["Weight"].values)
df["City"] = LOC["City"].values[loc_idx]
df["State"] = LOC["State"].values[loc_idx]
df["Location"] = LOC["Location"].values[loc_idx]
df["Road_Type"] = LOC["Road_Type"].values[loc_idx]
df["loc_risk"] = LOC["Risk"].values[loc_idx]

# --------------------------------------------------------------------------------------
# 4. TIME  (two rush-hour peaks on weekdays; late-night bump on weekends)
# --------------------------------------------------------------------------------------
hours = np.arange(24)
wd_hour = np.array([1.2, 0.8, 0.6, 0.6, 0.8, 1.6, 2.6, 4.2, 5.8, 5.2, 4.2, 4.0,
                    4.2, 4.0, 4.0, 4.4, 5.0, 6.2, 7.0, 6.4, 5.0, 3.6, 2.6, 1.8])
we_hour = np.array([3.2, 2.4, 1.8, 1.2, 1.0, 1.2, 1.8, 2.4, 3.2, 4.0, 4.6, 5.0,
                    5.2, 5.0, 4.8, 5.0, 5.4, 6.0, 6.6, 6.8, 6.4, 5.6, 4.8, 4.2])
wd_hour, we_hour = wd_hour / wd_hour.sum(), we_hour / we_hour.sum()
df["Hour"] = np.where(df["is_weekend"],
                      rng.choice(hours, size=N_ROWS, p=we_hour),
                      rng.choice(hours, size=N_ROWS, p=wd_hour))
minute = rng.integers(0, 60, size=N_ROWS)

# --------------------------------------------------------------------------------------
# 5. WEATHER  (monsoon Jun-Sep, winter fog in northern cities)
# --------------------------------------------------------------------------------------
weather = []
month = df["Date"].dt.month.values
for m, c in zip(month, df["City"].values):
    if m in (6, 7, 8, 9):                       # monsoon
        p = [0.40, 0.18, 0.22, 0.20, 0.00]
    elif m in (10, 11) and c in ("Chennai", "Coimbatore"):  # NE monsoon (TN)
        p = [0.45, 0.20, 0.20, 0.15, 0.00]
    elif m in (12, 1, 2) and c in NORTH_FOG_CITIES:         # winter fog
        p = [0.45, 0.20, 0.03, 0.02, 0.30]
    else:
        p = [0.68, 0.24, 0.05, 0.03, 0.00]
    weather.append(rng.choice(["Clear", "Cloudy", "Light Rain", "Heavy Rain", "Fog"], p=p))
df["Weather_Condition"] = weather

# --------------------------------------------------------------------------------------
# 6. ROAD CONDITION  (depends on weather)
# --------------------------------------------------------------------------------------
road_cond = []
for w in df["Weather_Condition"].values:
    if w in ("Light Rain", "Heavy Rain"):
        p = [0.00, 0.83, 0.10, 0.07]
    else:
        p = [0.80, 0.02, 0.12, 0.06]
    road_cond.append(rng.choice(["Dry", "Wet", "Damaged (Potholes)", "Under Construction"], p=p))
df["Road_Condition"] = road_cond

# --------------------------------------------------------------------------------------
# 7. SPEED LIMIT (depends on road type)
# --------------------------------------------------------------------------------------
speed_opts = {"Urban Road": ([30, 40, 50], [0.25, 0.50, 0.25]),
              "Rural Road": ([40, 50, 60], [0.30, 0.45, 0.25]),
              "Highway": ([60, 70, 80], [0.35, 0.35, 0.30]),
              "Expressway": ([80, 100, 120], [0.40, 0.45, 0.15])}
df["Speed_Limit"] = [rng.choice(speed_opts[r][0], p=speed_opts[r][1]) for r in df["Road_Type"]]

# --------------------------------------------------------------------------------------
# 8. LIGHT CONDITION (derived from hour, so it is internally consistent)
# --------------------------------------------------------------------------------------
def light_for(hour, road_type):
    if 6 <= hour <= 17:
        return "Daylight"
    if hour in (5, 18, 19):
        return "Dawn/Dusk"
    lit_prob = {"Urban Road": 0.85, "Expressway": 0.75, "Highway": 0.50, "Rural Road": 0.15}[road_type]
    return "Darkness - Lights Lit" if rng.random() < lit_prob else "Darkness - No Lights"

df["Light_Condition"] = [light_for(h, r) for h, r in zip(df["Hour"], df["Road_Type"])]
is_night = df["Hour"].isin([21, 22, 23, 0, 1, 2, 3, 4]).values

# --------------------------------------------------------------------------------------
# 9. VEHICLE TYPE, NUMBER OF VEHICLES
# --------------------------------------------------------------------------------------
veh_names = ["Two-Wheeler", "Car", "Truck", "Bus", "Auto-Rickshaw", "Bicycle", "Van/LCV"]
veh_base = np.array([0.40, 0.22, 0.11, 0.06, 0.09, 0.04, 0.08])
vehicle = []
for r in df["Road_Type"].values:
    p = veh_base.copy()
    if r in ("Highway", "Expressway"):
        p = p * np.array([0.70, 1.30, 2.00, 1.80, 0.20, 0.10, 1.20])
    elif r == "Urban Road":
        p = p * np.array([1.15, 0.95, 0.60, 0.80, 1.30, 1.20, 0.90])
    p = p / p.sum()
    vehicle.append(rng.choice(veh_names, p=p))
df["Vehicle_Type"] = vehicle

extra_veh = rng.poisson(0.55, size=N_ROWS)
extra_veh += np.isin(df["Vehicle_Type"], ["Truck", "Bus"]).astype(int) * rng.binomial(1, 0.35, size=N_ROWS)
df["Number_of_Vehicles"] = np.clip(1 + extra_veh, 1, 6)

# --------------------------------------------------------------------------------------
# 10. DRIVER AGE & GENDER
# --------------------------------------------------------------------------------------
age = np.where(rng.random(N_ROWS) < 0.55,
               rng.normal(28, 6, N_ROWS),     # young drivers
               rng.normal(46, 12, N_ROWS))    # older drivers
age = np.where(df["Vehicle_Type"].isin(["Truck", "Bus"]), rng.normal(41, 8, N_ROWS), age)
df["Driver_Age"] = np.clip(age.round(), 18, 78).astype(int)

female_p = df["Vehicle_Type"].map({"Two-Wheeler": 0.16, "Car": 0.18, "Truck": 0.005, "Bus": 0.01,
                                   "Auto-Rickshaw": 0.02, "Bicycle": 0.12, "Van/LCV": 0.04}).values
df["Driver_Gender"] = np.where(rng.random(N_ROWS) < female_p, "Female", "Male")

# --------------------------------------------------------------------------------------
# 11. ALCOHOL  (much more likely at night / weekends; rare among women, buses)
# --------------------------------------------------------------------------------------
alc_p = np.full(N_ROWS, 0.045)
alc_p = alc_p * np.where(is_night, 3.4, 1.0)
alc_p = alc_p * np.where(df["is_weekend"].values | (df["Date"].dt.dayofweek.values == 4), 1.5, 1.0)
alc_p = alc_p * np.where(df["Driver_Gender"].values == "Female", 0.15, 1.0)
alc_p = alc_p * np.where(df["Vehicle_Type"].values == "Bus", 0.3, 1.0)
alc_p = np.clip(alc_p, 0, 0.55)
df["Alcohol_Involved"] = np.where(rng.random(N_ROWS) < alc_p, "Yes", "No")

# --------------------------------------------------------------------------------------
# 12. SEVERITY  (driven by a hidden risk score + noise -> internally consistent)
# --------------------------------------------------------------------------------------
score = np.full(N_ROWS, 0.0)
score += (df["Speed_Limit"].values - 50) / 50 * 0.9
score += np.where(df["Alcohol_Involved"] == "Yes", 1.0, 0.0)
score += df["Weather_Condition"].map({"Clear": 0, "Cloudy": 0.05, "Light Rain": 0.15,
                                      "Heavy Rain": 0.40, "Fog": 0.55}).values
score += df["Road_Condition"].map({"Dry": 0, "Wet": 0.20, "Damaged (Potholes)": 0.25,
                                   "Under Construction": 0.10}).values
score += df["Light_Condition"].map({"Daylight": 0, "Dawn/Dusk": 0.10, "Darkness - Lights Lit": 0.25,
                                    "Darkness - No Lights": 0.65}).values
score += df["Vehicle_Type"].map({"Two-Wheeler": 0.35, "Car": -0.10, "Truck": 0.25, "Bus": 0.20,
                                 "Auto-Rickshaw": 0.10, "Bicycle": 0.30, "Van/LCV": 0.0}).values
score += df["Road_Type"].map({"Urban Road": -0.20, "Rural Road": 0.10, "Highway": 0.30, "Expressway": 0.40}).values
score += np.where(df["Driver_Age"] < 25, 0.15, 0) + np.where(df["Driver_Age"] > 60, 0.20, 0)
score += (df["Number_of_Vehicles"].values - 1) * 0.10
score += (df["loc_risk"].values - 1.0) * 1.2
score += rng.normal(0, 0.9, N_ROWS)          # randomness: same conditions can give different outcomes

cut_minor, cut_serious = np.quantile(score, [0.62, 0.91])    # ~62% minor, ~29% serious, ~9% fatal
df["Accident_Severity"] = np.select([score < cut_minor, score < cut_serious], ["Minor", "Serious"], "Fatal")

# --------------------------------------------------------------------------------------
# 13. CASUALTIES & FATALITIES (consistent with severity; casualties >= fatalities)
# --------------------------------------------------------------------------------------
bus_boost = np.where(df["Vehicle_Type"] == "Bus", 1.8, 1.0)
car_boost = np.where(df["Vehicle_Type"] == "Car", 1.2, 1.0)
multi = 1 + (df["Number_of_Vehicles"].values - 1) * 0.25
lam = bus_boost * car_boost * multi

casualties = np.zeros(N_ROWS, dtype=int)
fatalities = np.zeros(N_ROWS, dtype=int)
minor = (df["Accident_Severity"] == "Minor").values
serious = (df["Accident_Severity"] == "Serious").values
fatal = (df["Accident_Severity"] == "Fatal").values

casualties[minor] = rng.poisson(0.9 * lam[minor])
casualties[serious] = 1 + rng.poisson(1.0 * lam[serious])
fatalities[fatal] = 1 + rng.poisson(0.28 * lam[fatal])
casualties[fatal] = fatalities[fatal] + rng.poisson(0.9 * lam[fatal])

# A handful of genuine mass-casualty bus/truck crashes (legitimate outliers - kept & flagged in cleaning)
mass_idx = rng.choice(np.where(df["Vehicle_Type"].isin(["Bus", "Truck"]).values & fatal)[0], size=12, replace=False)
fatalities[mass_idx] = rng.integers(5, 14, size=12)
casualties[mass_idx] = fatalities[mass_idx] + rng.integers(8, 20, size=12)

df["Number_of_Casualties"] = casualties
df["Number_of_Fatalities"] = fatalities

# --------------------------------------------------------------------------------------
# 14. ASSEMBLE the clean "truth" table
# --------------------------------------------------------------------------------------
df = df.sort_values(["Date", "Hour"]).reset_index(drop=True)
df["Accident_ID"] = [f"ACC-{i:06d}" for i in range(1, len(df) + 1)]
df["Time"] = [f"{h:02d}:{m:02d}" for h, m in zip(df["Hour"], minute[:len(df)])]
df["Day_of_Week"] = df["Date"].dt.day_name()
df["Month"] = df["Date"].dt.month_name()
df["Year"] = df["Date"].dt.year
df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

cols = ["Accident_ID", "Date", "Time", "Day_of_Week", "Month", "Year", "Location", "City", "State",
        "Weather_Condition", "Road_Condition", "Road_Type", "Vehicle_Type", "Number_of_Vehicles",
        "Number_of_Casualties", "Number_of_Fatalities", "Accident_Severity", "Speed_Limit",
        "Light_Condition", "Alcohol_Involved", "Driver_Age", "Driver_Gender"]
df = df[cols].copy()

# --------------------------------------------------------------------------------------
# 15. INJECT REAL-WORLD DATA-QUALITY PROBLEMS (so cleaning is meaningful)
# --------------------------------------------------------------------------------------
def pick(frac):
    return rng.random(len(df)) < frac

# (a) missing values
for col, frac in [("Weather_Condition", 0.020), ("Road_Condition", 0.015), ("Light_Condition", 0.010),
                  ("Driver_Age", 0.030), ("Driver_Gender", 0.020), ("Speed_Limit", 0.010),
                  ("Alcohol_Involved", 0.020)]:
    df[col] = df[col].astype(object)
    df.loc[pick(frac), col] = np.nan

# (b) inconsistent text: case, spaces, spelling variants
def messy(series, variants, frac):
    series = series.astype(object)
    mask = pick(frac) & series.notna().values
    series.loc[mask] = [rng.choice(variants.get(v, [v.upper(), v.lower(), " " + v + " "])) for v in series[mask]]
    return series

df["City"] = messy(df["City"], {}, 0.04)
df["Weather_Condition"] = messy(df["Weather_Condition"], {"Light Rain": ["light rain", "LIGHT RAIN", "Drizzle"],
                                                          "Heavy Rain": ["heavy rain", "Heavy rain", "Storm"]}, 0.04)
df["Vehicle_Type"] = messy(df["Vehicle_Type"], {"Two-Wheeler": ["Two Wheeler", "two wheeler", "2-Wheeler", "Bike"],
                                                "Auto-Rickshaw": ["Auto Rickshaw", "auto", "Rickshaw"],
                                                "Van/LCV": ["Van", "LCV"]}, 0.05)
df["Accident_Severity"] = messy(df["Accident_Severity"], {}, 0.03)
df["Alcohol_Involved"] = messy(df["Alcohol_Involved"], {"Yes": ["Y", "yes", "YES"], "No": ["N", "no", "NO"]}, 0.05)
df["Driver_Gender"] = messy(df["Driver_Gender"], {"Male": ["M", "male"], "Female": ["F", "female"]}, 0.04)

# (c) a few dates in a different format (DD/MM/YYYY)
mask = pick(0.015)
df.loc[mask, "Date"] = pd.to_datetime(df.loc[mask, "Date"]).dt.strftime("%d/%m/%Y")

# (d) invalid / impossible values
df["Driver_Age"] = df["Driver_Age"].astype(object)
bad = rng.choice(len(df), size=45, replace=False)
df.loc[bad, "Driver_Age"] = rng.choice([0, -5, 5, 123, 150, 999], size=45)
bad = rng.choice(len(df), size=25, replace=False)
df.loc[bad, "Speed_Limit"] = rng.choice([0, 5, 400, 999], size=25)
bad = rng.choice(len(df), size=20, replace=False)
df.loc[bad, "Number_of_Vehicles"] = 0
bad = rng.choice(np.where(df["Number_of_Casualties"] > 0)[0], size=25, replace=False)
df.loc[bad, "Number_of_Fatalities"] = df.loc[bad, "Number_of_Casualties"] + 1     # fatalities > casualties (impossible)

# (e) exact duplicate rows (double data entry)
dups = df.sample(n=160, random_state=SEED)
df = pd.concat([df, dups], ignore_index=True).sample(frac=1, random_state=SEED).reset_index(drop=True)
df = df.sort_values("Accident_ID", kind="stable").reset_index(drop=True)

OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT_FILE, index=False)
print(f"Raw dataset created: {OUT_FILE}")
print(f"Rows: {len(df):,} | Columns: {df.shape[1]}")
print(df.head())
