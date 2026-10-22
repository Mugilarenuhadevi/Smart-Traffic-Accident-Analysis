"""
exploratory_analysis.py
-----------------------
STEP 3 of the pipeline:  cleaned CSV  ->  charts + written insights

Input : data/cleaned/cleaned_accidents.csv
Output: visualizations/*.png          (19 charts)
        docs/key_insights.md          (findings + recommendations CALCULATED from the data)

Run:
    python python/exploratory_analysis.py

Nothing in the insights file is typed by hand: every number is computed from the dataset,
so if you regenerate the data the insights update automatically.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")          # save charts to files (no pop-up windows) - works on any machine
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
CLEAN_FILE = ROOT / "data" / "cleaned" / "cleaned_accidents.csv"
VIZ_DIR = ROOT / "visualizations"
INSIGHTS_FILE = ROOT / "docs" / "key_insights.md"

SEVERITY_ORDER = ["Minor", "Serious", "Fatal"]
SEVERITY_COLORS = {"Minor": "#2E9E6B", "Serious": "#F2A33A", "Fatal": "#C8372D"}
MONTH_ORDER = ["January", "February", "March", "April", "May", "June", "July", "August",
               "September", "October", "November", "December"]
DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
BLUE = "#2F6DB5"

sns.set_theme(style="whitegrid", context="notebook")
plt.rcParams.update({"figure.dpi": 110, "axes.titlesize": 14, "axes.titleweight": "bold",
                     "axes.labelsize": 11})


# ------------------------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------------------------
def save(fig, name):
    VIZ_DIR.mkdir(exist_ok=True)
    fig.tight_layout()
    fig.savefig(VIZ_DIR / name, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved visualizations/{name}")


def bar_counts(series, title, xlabel, name, order=None, horizontal=False, color=BLUE, top=None):
    """Bar chart of how many accidents fall in each category (with value labels)."""
    counts = series.value_counts()
    if order is not None:
        counts = counts.reindex([o for o in order if o in counts.index])
    elif top:
        counts = counts.head(top)
    fig, ax = plt.subplots(figsize=(9, 5.5 if horizontal else 5))
    if horizontal:
        counts = counts.iloc[::-1]
        ax.barh(counts.index.astype(str), counts.values, color=color)
        ax.set_xlabel("Number of accidents")
        ax.set_ylabel(xlabel)
        for i, v in enumerate(counts.values):
            ax.text(v, i, f" {v:,}", va="center", fontsize=9)
        ax.set_xlim(0, counts.max() * 1.12)
    else:
        ax.bar(counts.index.astype(str), counts.values, color=color)
        ax.set_ylabel("Number of accidents")
        ax.set_xlabel(xlabel)
        for i, v in enumerate(counts.values):
            ax.text(i, v, f"{v:,}", ha="center", va="bottom", fontsize=9)
        ax.set_ylim(0, counts.max() * 1.12)
        plt.setp(ax.get_xticklabels(), rotation=30 if len(counts) > 6 else 0, ha="right" if len(counts) > 6 else "center")
    ax.set_title(title)
    save(fig, name)


def stacked_pct(df, col, title, xlabel, name, order=None):
    """100% stacked bar: share of Minor / Serious / Fatal inside each category of `col`."""
    ct = pd.crosstab(df[col], df["Accident_Severity"], normalize="index")[SEVERITY_ORDER] * 100
    if order is not None:
        ct = ct.reindex([o for o in order if o in ct.index])
    fig, ax = plt.subplots(figsize=(9, 5.2))
    ct.plot(kind="bar", stacked=True, ax=ax, color=[SEVERITY_COLORS[s] for s in SEVERITY_ORDER], width=0.75)
    ax.set_ylabel("% of accidents")
    ax.set_xlabel(xlabel)
    ax.set_title(title)
    ax.legend(title="Severity", bbox_to_anchor=(1.01, 1), loc="upper left")
    for container, sev in zip(ax.containers, SEVERITY_ORDER):
        labels = [f"{v:.0f}%" if v >= 6 else "" for v in ct[sev]]
        ax.bar_label(container, labels=labels, label_type="center", color="white", fontsize=8, fontweight="bold")
    plt.setp(ax.get_xticklabels(), rotation=0 if len(ct) <= 6 else 30, ha="center" if len(ct) <= 6 else "right")
    save(fig, name)
    return ct


def severe_rate(df, col, min_n=1, exclude=("Unknown",)):
    """Table per category: accidents, severe% (Serious+Fatal), fatal% (accidents that were Fatal)."""
    d = df[~df[col].isin(exclude)]
    g = d.groupby(col).agg(accidents=("Accident_ID", "count"),
                           fatalities=("Number_of_Fatalities", "sum"),
                           severe_pct=("Accident_Severity", lambda s: (s != "Minor").mean() * 100),
                           fatal_pct=("Accident_Severity", lambda s: (s == "Fatal").mean() * 100))
    return g[g["accidents"] >= min_n].round(1)


# ------------------------------------------------------------------------------------
# the 16 requested analyses (+ extras)
# ------------------------------------------------------------------------------------
def make_charts(df):
    print("Creating charts ...")

    # 1. Accidents by year
    bar_counts(df["Year"], "Accidents by Year", "Year", "01_accidents_by_year.png",
               order=sorted(df["Year"].unique()))
    # 2. Accidents by month
    bar_counts(df["Month"], "Accidents by Month", "Month", "02_accidents_by_month.png", order=MONTH_ORDER)
    # 3. Accidents by day of week
    bar_counts(df["Day_of_Week"], "Accidents by Day of Week", "Day", "03_accidents_by_day_of_week.png",
               order=DAY_ORDER)

    # 4. Accidents by hour (line chart shows the rush-hour peaks clearly)
    by_hour = df.groupby("Hour").size()
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(by_hour.index, by_hour.values, marker="o", color=BLUE, linewidth=2)
    ax.fill_between(by_hour.index, by_hour.values, alpha=0.15, color=BLUE)
    peak_h = by_hour.idxmax()
    ax.annotate(f"Peak: {peak_h}:00\n({by_hour.max():,} accidents)", xy=(peak_h, by_hour.max()),
                xytext=(peak_h - 6, by_hour.max() * 0.93), arrowprops=dict(arrowstyle="->"), fontsize=10)
    ax.set_xticks(range(0, 24))
    ax.set_xlabel("Hour of day (24h)")
    ax.set_ylabel("Number of accidents")
    ax.set_title("Accidents by Hour of Day")
    save(fig, "04_accidents_by_hour.png")

    # 5-8. weather, road condition, road type, vehicle type
    bar_counts(df["Weather_Condition"], "Accidents by Weather Condition", "Weather", "05_accidents_by_weather.png")
    bar_counts(df["Road_Condition"], "Accidents by Road Condition", "Road condition", "06_accidents_by_road_condition.png")
    bar_counts(df["Road_Type"], "Accidents by Road Type", "Road type", "07_accidents_by_road_type.png")
    bar_counts(df["Vehicle_Type"], "Accidents by Vehicle Type", "Vehicle type", "08_accidents_by_vehicle_type.png",
               horizontal=True)

    # 9. Severity distribution
    sev = df["Accident_Severity"].value_counts().reindex(SEVERITY_ORDER)
    fig, ax = plt.subplots(figsize=(6.5, 6))
    ax.pie(sev.values, labels=[f"{k}\n{v:,}" for k, v in sev.items()], autopct="%1.1f%%", startangle=90,
           colors=[SEVERITY_COLORS[s] for s in SEVERITY_ORDER], wedgeprops=dict(width=0.45, edgecolor="white"),
           textprops={"fontsize": 11})
    ax.set_title("Accident Severity Distribution")
    save(fig, "09_severity_distribution.png")

    # 10. Location / city
    bar_counts(df["City"], "Accidents by City", "City", "10a_accidents_by_city.png", horizontal=True)
    bar_counts(df["Location"], "Top 10 Accident Locations (by number of accidents)", "Location",
               "10b_top10_locations.png", horizontal=True, top=10)

    # 11-12. Fatalities & casualties by year
    for col, name, fname in [("Number_of_Fatalities", "Fatalities", "11_fatalities_by_year.png"),
                             ("Number_of_Casualties", "Casualties", "12_casualties_by_year.png")]:
        s = df.groupby("Year")[col].sum()
        fig, ax = plt.subplots(figsize=(8.5, 5))
        ax.plot(s.index, s.values, marker="o", linewidth=2.5, color="#C8372D" if name == "Fatalities" else "#7B4FB5")
        for x, y in zip(s.index, s.values):
            ax.text(x, y, f"{y:,}", ha="center", va="bottom", fontsize=10)
        ax.set_xticks(s.index)
        ax.set_ylim(0, s.max() * 1.15)
        ax.set_xlabel("Year")
        ax.set_ylabel(f"Total {name.lower()}")
        ax.set_title(f"Total {name} by Year")
        save(fig, fname)

    # 13. Alcohol involvement (share of accidents + severity split)
    known = df[df["Alcohol_Involved"] != "Unknown"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    cnt = known["Alcohol_Involved"].value_counts()
    axes[0].pie(cnt.values, labels=cnt.index, autopct="%1.1f%%", startangle=90,
                colors=["#9AA5B1", "#C8372D"] if cnt.index[0] == "No" else ["#C8372D", "#9AA5B1"],
                wedgeprops=dict(edgecolor="white"))
    axes[0].set_title("Alcohol Involved in Accident?")
    ct = pd.crosstab(known["Alcohol_Involved"], known["Accident_Severity"], normalize="index")[SEVERITY_ORDER] * 100
    ct.plot(kind="bar", stacked=True, ax=axes[1], color=[SEVERITY_COLORS[s] for s in SEVERITY_ORDER], width=0.6)
    for container, s in zip(axes[1].containers, SEVERITY_ORDER):
        axes[1].bar_label(container, labels=[f"{v:.0f}%" for v in ct[s]], label_type="center", color="white",
                          fontweight="bold")
    axes[1].set_title("Severity: Alcohol vs No Alcohol")
    axes[1].set_ylabel("% of accidents")
    axes[1].set_xlabel("Alcohol involved")
    plt.setp(axes[1].get_xticklabels(), rotation=0)
    axes[1].legend(title="Severity", bbox_to_anchor=(1.01, 1), loc="upper left")
    save(fig, "13_alcohol_involvement.png")

    # 14-16. Speed limit / age group / light condition vs severity
    stacked_pct(df, "Speed_Limit", "Speed Limit vs Accident Severity", "Speed limit (km/h)",
                "14_speed_limit_vs_severity.png", order=sorted(df["Speed_Limit"].unique()))
    stacked_pct(df, "Age_Group", "Driver Age Group vs Accident Severity", "Driver age group",
                "15_age_group_vs_severity.png", order=["18-24", "25-34", "35-49", "50-64", "65+"])
    stacked_pct(df, "Light_Condition", "Light Condition vs Accident Severity", "Light condition",
                "16_light_condition_vs_severity.png",
                order=["Daylight", "Dawn/Dusk", "Darkness - Lights Lit", "Darkness - No Lights"])

    # ---- extras -------------------------------------------------------------------
    # 17. Heat-map day x hour
    pivot = df.pivot_table(index="Day_of_Week", columns="Hour", values="Accident_ID", aggfunc="count").reindex(DAY_ORDER)
    fig, ax = plt.subplots(figsize=(13, 5))
    sns.heatmap(pivot, cmap="YlOrRd", ax=ax, linewidths=0.3, cbar_kws={"label": "Accidents"})
    ax.set_title("When do accidents happen? Day of Week x Hour of Day")
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("")
    save(fig, "17_heatmap_day_hour.png")

    # 18. Severity by vehicle type
    stacked_pct(df, "Vehicle_Type", "Severity by Vehicle Type", "Vehicle type", "18_severity_by_vehicle_type.png",
                order=df["Vehicle_Type"].value_counts().index.tolist())

    # 19. Highest-risk locations (fatal accidents per 100 accidents, min 150 accidents)
    loc = severe_rate(df, "Location", min_n=150).sort_values("fatal_pct", ascending=False).head(10).iloc[::-1]
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    ax.barh(loc.index, loc["fatal_pct"], color="#C8372D")
    for i, v in enumerate(loc["fatal_pct"]):
        ax.text(v, i, f" {v:.1f}%", va="center", fontsize=9)
    ax.set_xlabel("% of accidents that were fatal")
    ax.set_title("Top 10 High-Risk Locations (fatal-accident share, min. 150 accidents)")
    ax.set_xlim(0, loc["fatal_pct"].max() * 1.15)
    save(fig, "19_high_risk_locations.png")


# ------------------------------------------------------------------------------------
# insights calculated from the data
# ------------------------------------------------------------------------------------
def build_insights(df):
    n = len(df)
    tot_cas, tot_fat = int(df["Number_of_Casualties"].sum()), int(df["Number_of_Fatalities"].sum())
    L = []  # lines of markdown

    def add(*lines):
        L.extend(lines)

    add("# Key Insights & Recommendations", "",
        "> Every number below is calculated from `data/cleaned/cleaned_accidents.csv` by "
        "`python/exploratory_analysis.py`.", "",
        "**Definitions:** *Severe* = Serious or Fatal accident. *Fatal %* = share of accidents classified Fatal. "
        "*Fatality rate* = fatalities per 100 casualties.", "")

    # ---- overview
    by_year = df.groupby("Year").size()
    add("## 0. Overview", "",
        f"- **{n:,}** accidents, **{tot_cas:,}** casualties, **{tot_fat:,}** fatalities "
        f"({tot_fat / tot_cas * 100:.1f} deaths per 100 casualties; {tot_cas / n:.2f} casualties per accident).",
        f"- Period: {df['Date'].min()} to {df['Date'].max()}. Busiest year: **{by_year.idxmax()}** "
        f"({by_year.max():,}); quietest: **{by_year.idxmin()}** ({by_year.min():,}).",
        f"- Severity mix: " + ", ".join(f"{k} {v:.1f}%" for k, v in
                                       (df['Accident_Severity'].value_counts(normalize=True)[SEVERITY_ORDER] * 100).items()) + ".", "")

    recs = []

    # ---- 1. time
    by_hour = df.groupby("Hour").size()
    top3h = by_hour.sort_values(ascending=False).head(3)
    period = df.groupby("Time_Period").agg(acc=("Accident_ID", "count"),
                                           fatal=("Accident_Severity", lambda s: (s == "Fatal").mean() * 100)).round(1)
    by_dow = df["Day_of_Week"].value_counts()
    by_month = df["Month"].value_counts()
    night_fatal = period.loc["Late Night (12-4 AM)", "fatal"]
    day_fatal = period.loc["Midday (11 AM-3 PM)", "fatal"]
    top2d = by_dow.head(2).index.tolist()
    add("## 1. When do accidents happen?", "",
        f"- **DATA FINDING:** Peak hours are {', '.join(f'{h}:00 ({c:,})' for h, c in top3h.items())}. "
        f"Busiest day: **{by_dow.idxmax()}** ({by_dow.max():,}); quietest: {by_dow.idxmin()} ({by_dow.min():,}). "
        f"Busiest month: **{by_month.idxmax()}** ({by_month.max():,}).",
        f"- **DATA FINDING:** Late-night accidents (12-4 AM) are fewer ({period.loc['Late Night (12-4 AM)', 'acc']:,} vs "
        f"{period.loc['Evening Peak (4-8 PM)', 'acc']:,} in the 4-8 PM peak) but deadlier: {night_fatal:.1f}% fatal vs "
        f"{day_fatal:.1f}% at midday.",
        f"- **RECOMMENDATION:** Concentrate traffic police and ambulance coverage between "
        f"{min(top3h.index)}:00 and {max(top3h.index) + 1}:00 (highest volume); add separate drunk-driving and speed "
        "checks at night, because fewer accidents there still end more often in death.", "")
    recs.append("High-risk time monitoring")

    # ---- 2. weather
    w = severe_rate(df, "Weather_Condition", min_n=50).sort_values("severe_pct", ascending=False)
    clear_sev = w.loc["Clear", "severe_pct"]
    add("## 2. Weather", "",
        "- **DATA FINDING:** Share of severe accidents by weather: " +
        "; ".join(f"{i} {r.severe_pct:.1f}% (fatal {r.fatal_pct:.1f}%)" for i, r in w.iterrows()) + ".",
        f"- **DATA FINDING:** **{w.index[0]}** is the most severe condition: {w.iloc[0]['severe_pct']:.1f}% severe "
        f"vs {clear_sev:.1f}% in clear weather.",
        f"- **RECOMMENDATION:** Trigger weather-based alerts (SMS / variable-message signs) for {w.index[0].lower()} and "
        f"{w.index[1].lower()}, with temporary speed reductions and fog lights on the affected corridors.", "")
    recs.append("Weather-related warnings")

    # ---- 3. road condition
    rc = severe_rate(df, "Road_Condition", min_n=50).sort_values("severe_pct", ascending=False)
    add("## 3. Road condition", "",
        "- **DATA FINDING:** Severe-accident share by road condition: " +
        "; ".join(f"{i} {r.severe_pct:.1f}%" for i, r in rc.iterrows()) + ".",
        f"- **DATA FINDING:** Compared with dry roads ({rc.loc['Dry', 'severe_pct']:.1f}% severe), wet roads are "
        f"{rc.loc['Wet', 'severe_pct'] - rc.loc['Dry', 'severe_pct']:+.1f} points and damaged roads "
        f"{rc.loc['Damaged (Potholes)', 'severe_pct'] - rc.loc['Dry', 'severe_pct']:+.1f} points.",
        "- **RECOMMENDATION:** Resurface pothole-damaged stretches, improve drainage and anti-skid surfacing where "
        "roads are often wet, and add warning signs / barriers around construction zones.", "")
    recs.append("Road safety improvements")

    # ---- 4. vehicles
    vt = severe_rate(df, "Vehicle_Type", min_n=50, exclude=()).sort_values("accidents", ascending=False)
    worst_v = vt.sort_values("fatal_pct", ascending=False)
    add("## 4. Vehicle types", "",
        f"- **DATA FINDING:** Most frequent: **{vt.index[0]}** ({vt.iloc[0]['accidents']:,.0f} accidents, "
        f"{vt.iloc[0]['accidents'] / n * 100:.1f}%), then {vt.index[1]} ({vt.iloc[1]['accidents'] / n * 100:.1f}%) "
        f"and {vt.index[2]} ({vt.iloc[2]['accidents'] / n * 100:.1f}%).",
        f"- **DATA FINDING:** Highest fatal share: **{worst_v.index[0]}** ({worst_v.iloc[0]['fatal_pct']:.1f}%), then "
        f"{worst_v.index[1]} ({worst_v.iloc[1]['fatal_pct']:.1f}%).",
        f"- **RECOMMENDATION:** Run helmet / rider-safety campaigns and enforcement aimed at {vt.index[0].lower()} users; "
        f"add speed limiters and driver-fatigue rules for {worst_v.index[0].lower()} operators.", "")

    # ---- 5. locations
    loc = severe_rate(df, "Location", min_n=100)
    loc["city"] = df.drop_duplicates("Location").set_index("Location")["City"]
    top_cnt = loc.sort_values("accidents", ascending=False).head(3)
    top_fat = loc.sort_values("fatal_pct", ascending=False).head(3)
    city = df.groupby("City").agg(acc=("Accident_ID", "count"), fat=("Number_of_Fatalities", "sum")).sort_values("acc", ascending=False)
    add("## 5. Locations", "",
        f"- **DATA FINDING:** Most accidents: {', '.join(f'{i} ({r.accidents:,.0f})' for i, r in top_cnt.iterrows())}.",
        f"- **DATA FINDING:** Highest fatal share: " +
        ", ".join(f"{i} - {r.city} ({r.fatal_pct:.1f}% fatal)" for i, r in top_fat.iterrows()) + ".",
        f"- **DATA FINDING:** City with most accidents: **{city.index[0]}** ({city.iloc[0]['acc']:,}); "
        f"most fatalities: **{city['fat'].idxmax()}** ({city['fat'].max():,}).",
        f"- **RECOMMENDATION:** Install speed cameras, better lighting and emergency response points at "
        f"{top_fat.index[0]} and {top_fat.index[1]} first, because the same number of accidents there costs more lives.", "")
    recs.append("Emergency response planning")

    # ---- 6. alcohol
    al = df[df["Alcohol_Involved"] != "Unknown"]
    a_yes = (al["Alcohol_Involved"] == "Yes").mean() * 100
    fy = (al[al["Alcohol_Involved"] == "Yes"]["Accident_Severity"] == "Fatal").mean() * 100
    fn = (al[al["Alcohol_Involved"] == "No"]["Accident_Severity"] == "Fatal").mean() * 100
    night = al[al["Hour"].isin([21, 22, 23, 0, 1, 2, 3, 4])]
    a_night = (night["Alcohol_Involved"] == "Yes").mean() * 100
    a_day = (al[~al.index.isin(night.index)]["Alcohol_Involved"] == "Yes").mean() * 100
    add("## 6. Alcohol", "",
        f"- **DATA FINDING:** Alcohol was involved in **{a_yes:.1f}%** of accidents with a known alcohol status.",
        f"- **DATA FINDING:** {fy:.1f}% of alcohol-related accidents were fatal vs {fn:.1f}% of the others "
        f"(**{fy / fn:.1f}x** higher).",
        f"- **DATA FINDING:** Alcohol share is {a_night:.1f}% between 9 PM-4 AM vs {a_day:.1f}% during the rest of the day.",
        "- **RECOMMENDATION:** Run breathalyser checkpoints at night and on weekends at the highest-risk locations, "
        "and fund a public awareness campaign on drink-driving.", "")
    recs.append("Driver awareness programs")

    # ---- 7. weekend vs weekday
    wk = df.groupby("Day_Type").agg(acc=("Accident_ID", "count"),
                                    severe=("Accident_Severity", lambda s: (s != "Minor").mean() * 100),
                                    fatal=("Accident_Severity", lambda s: (s == "Fatal").mean() * 100))
    n_days = df.groupby("Day_Type")["Date"].nunique()
    per_day = wk["acc"] / n_days
    a_wk = al.groupby("Day_Type")["Alcohol_Involved"].apply(lambda s: (s == "Yes").mean() * 100)
    add("## 7. Weekend vs weekday", "",
        f"- **DATA FINDING:** Weekend days average {per_day['Weekend']:.1f} accidents per day vs "
        f"{per_day['Weekday']:.1f} on weekdays. Fatal share: weekend {wk.loc['Weekend', 'fatal']:.1f}% vs weekday "
        f"{wk.loc['Weekday', 'fatal']:.1f}%. Alcohol share: weekend {a_wk['Weekend']:.1f}% vs weekday {a_wk['Weekday']:.1f}%.",
        f"- **RECOMMENDATION:** Schedule extra patrols and trauma-centre staffing on the busiest days "
        f"({' and '.join(top2d)}) and on weekend nights, rather than spreading resources evenly across the week.", "")

    # ---- 8. speed, light, age
    sp = severe_rate(df, "Speed_Limit", min_n=30, exclude=())
    li = severe_rate(df, "Light_Condition", min_n=30, exclude=())
    ag = severe_rate(df, "Age_Group", min_n=30, exclude=())
    add("## 8. Speed, lighting and driver age", "",
        "- **DATA FINDING (speed):** Fatal share by speed limit: " +
        ", ".join(f"{int(i)} km/h {r.fatal_pct:.1f}%" for i, r in sp.iterrows()) + ". "
        "Caution: speed limit is linked to road type (high limits are on expressways/highways), so this shows "
        "the *environment's* risk, not only driver speed.",
        "- **DATA FINDING (lighting):** Fatal share by light condition: " +
        ", ".join(f"{i} {r.fatal_pct:.1f}%" for i, r in li.iterrows()) + ".",
        "- **DATA FINDING (age):** Fatal share by driver age group: " +
        ", ".join(f"{i} {r.fatal_pct:.1f}%" for i, r in ag.iterrows()) + ".",
        "- **RECOMMENDATION (speed):** Enforce limits with average-speed cameras on the highest-limit corridors; "
        "add rumble strips and median barriers on expressways.",
        f"- **RECOMMENDATION (lighting):** Fix street lighting on unlit stretches - **{li['fatal_pct'].idxmax()}** has "
        f"the highest fatal share ({li['fatal_pct'].max():.1f}%).",
        (f"- **RECOMMENDATION (age):** Target refresher training at the **{ag['fatal_pct'].idxmax()}** group "
         f"({ag['fatal_pct'].max():.1f}% fatal)." if ag['fatal_pct'].max() - ag['fatal_pct'].min() >= 3 else
         f"- **DATA FINDING (age):** Fatal share differs by only {ag['fatal_pct'].max() - ag['fatal_pct'].min():.1f} "
         "points between age groups, so age alone is NOT a strong risk factor here; "
         "road and environment factors matter more."), "")
    recs.append("Speed management")

    # ---- risk categories
    rk = df["Risk_Category"].value_counts(normalize=True).reindex(["Low", "Medium", "High", "Critical"]) * 100
    add("## 9. Risk categories", "",
        "- **DATA FINDING:** " + ", ".join(f"{k} {v:.1f}%" for k, v in rk.items()) +
        " of accidents (rule-based `Risk_Category`; see data_cleaning.py).",
        f"- **DATA FINDING:** {int(df['Mass_Casualty_Flag'].sum())} mass-casualty accidents (10+ casualties) = "
        f"{df['Mass_Casualty_Flag'].mean() * 100:.2f}% of accidents but {df.loc[df['Mass_Casualty_Flag'] == 1, 'Number_of_Fatalities'].sum() / tot_fat * 100:.1f}% "
        f"of all fatalities; {df.loc[df['Mass_Casualty_Flag'] == 1, 'Vehicle_Type'].value_counts().idxmax()}s are the most "
        "common vehicle in these events.",
        "- **RECOMMENDATION:** Pre-plan multi-ambulance dispatch rules for heavy-vehicle crashes on highways "
        "(they generate the mass-casualty events).", "")

    return "\n".join(L), {"recommendation_areas": recs}


def main():
    if not CLEAN_FILE.exists():
        raise SystemExit(f"{CLEAN_FILE} not found. Run python python/data_cleaning.py first.")
    df = pd.read_csv(CLEAN_FILE)
    print(f"Loaded {len(df):,} rows, {df.shape[1]} columns")
    make_charts(df)
    text, _ = build_insights(df)
    INSIGHTS_FILE.parent.mkdir(exist_ok=True)
    INSIGHTS_FILE.write_text(text, encoding="utf-8")
    print("\n" + text)
    print(f"\nInsights saved -> {INSIGHTS_FILE}")


if __name__ == "__main__":
    main()
