# Interview Preparation - Smart Traffic Accident Risk Analysis

> **Be honest about the data.** The dataset is *synthetic but realistic* (generated with a fixed seed, with severity driven by
> real-world risk factors and deliberate data-quality problems). Say so in the first minute - interviewers respect it, and
> it lets you talk about the generator as an extra skill. Never present the findings as real Indian statistics.
> Say: *"The methodology is what I want to show; the pipeline works unchanged on a real dataset such as UK STATS19."*

## Key numbers to memorise
| Item | Value |
|---|---|
| Raw → cleaned rows | 12,160 → 12,000 (160 duplicates removed) |
| Columns | 22 raw → 33 cleaned |
| Total accidents / casualties / fatalities | 12,000 / 19,839 / 1,634 |
| Fatality rate | 8.24 deaths per 100 casualties |
| Avg casualties per accident | 1.65 |
| Severity mix | Minor 61.9% · Serious 28.9% · Fatal 9.2% |
| Peak hours | 18:00 (965), 19:00 (925), 17:00 (760) |
| Busiest day / month | Saturday (1,930) / October (1,144) |
| Weather: severe-accident share | Fog 52.4% · Heavy rain 50.2% · Clear 35.1% |
| Alcohol | 6.5% of accidents; 29.7% fatal vs 7.6% (3.9×) |
| Highest fatal-share location | Mumbai-Pune Expressway Khandala, 33.8% |
| Most accidents | NH44 Singhu Border, 420 |
| Risk-factor stacking | fatal 2.3% (0 factors) → 60.0% (3+ factors) |

---------------------------------------------------------------------------------------------------

## A. 60-second explanation
> "I built an end-to-end analytics project on road accidents. I started with about 12,000 accident records - generated
> synthetically so I could control realism and build in real-world data problems like duplicates, typos and impossible values.
> I cleaned them with Python and Pandas, explored them to see when, where and why accidents become severe, loaded the clean data
> into MySQL, answered 29 business questions with SQL, and built a four-page Power BI dashboard.
> The main insight is that *frequency and severity are different things*: the busiest evening rush hour has the most accidents,
> but late-night accidents are more than twice as likely to be fatal - 15.6% versus 6.9% at midday. Alcohol makes an accident
> about four times more likely to be fatal, and risks stack: with three or more risk factors, 60% of accidents are fatal
> versus 2% with none. I turned that into recommendations such as night-time drink-driving checks, weather alerts and
> fixing the highest-fatality expressway locations first."

## B. 2-minute explanation
> "The goal was to help a road-safety authority decide where to act first, so I treated it like a real business problem.
>
> **Data.** I generated 12,000 records for ten Indian cities across 2019-2023. Severity isn't random - I modelled it from speed limit,
> alcohol, weather, lighting, road condition, vehicle and location, and added seasonality like monsoon, fog and a lockdown dip in 2020.
> I also injected dirt on purpose: 160 duplicates, 40 different spellings of ten city names, two date formats, ages like 150 and
> fatalities greater than casualties.
>
> **Cleaning.** In Pandas I removed duplicates, standardised categories with mapping dictionaries, parsed dates explicitly, and fixed
> impossible values using rules I can justify - for example median age by vehicle type, and the most common speed limit for the road type.
> I derived light condition from the hour, labelled unknown weather and alcohol as 'Unknown' rather than guessing, and kept extreme
> bus-crash casualty counts but flagged them, because they are real events. Then I created features like hour, weekend flag, age group,
> fatality rate and a rule-based risk category.
>
> **EDA and SQL.** I made 19 charts, then loaded the data into MySQL with a primary key and indexes and wrote 29 queries - CTEs,
> window functions like LAG and RANK, CASE pivots and joins - to answer questions such as top-10 high-risk locations,
> weekend versus weekday per day, and severity by weather.
>
> **Power BI.** The dashboard has an executive overview, risk analysis, location and vehicle page, and an insights page, with six
> synced slicers and DAX measures like fatality rate and alcohol-related accidents. My KPI cards reconcile exactly with SQL and Python.
>
> **Findings.** Peak volume is 5-8 PM but late night is deadliest; fog and heavy rain push severe accidents to about 50% versus 35% in
> clear weather; trucks and buses have the highest fatal share; and the busiest location isn't the deadliest. My recommendations are
> separated clearly into data finding and action."

---------------------------------------------------------------------------------------------------

## C & D. Ten common interview questions with strong, simple answers

**1. Why did you choose this project?**
Road safety is a real problem where analytics has a clear decision at the end - where to send police, repair roads, run campaigns.
It let me practise the whole analyst workflow (clean → explore → SQL → dashboard → recommendations) on one story.

**2. Your data is synthetic. Why, and does that weaken the project?**
I wanted control over size and columns and to add realistic data-quality problems so cleaning had real work to do. It means the findings
describe this dataset, not real statistics - I say that openly. What the project demonstrates is the *method*, and the code works on a
real dataset (e.g. UK STATS19) after mapping column names. I also know how I built the relationships, so I can explain why each pattern appears.

**3. What was the hardest data-cleaning decision?**
Missing alcohol status. If I filled it with "No", I'd understate alcohol-related accidents. So I labelled it 'Unknown', kept the row for
totals, and excluded 'Unknown' in alcohol comparisons. Rule: don't invent information when guessing could bias a conclusion.

**4. How did you handle outliers?**
I checked casualties with the IQR rule. The large values were mass-casualty bus/truck crashes - real events, not errors. Removing them would hide the
most important accidents, so I kept them and added `Mass_Casualty_Flag`. They are 0.11% of accidents but 6.9% of all fatalities, which is a finding in itself.
Impossible values (age 150, speed limit 999) I treated as errors and fixed.

**5. What is your most important insight?**
Frequency ≠ severity. 5-8 PM has the most accidents, but 12-4 AM has 15.6% fatal accidents versus 6.9% at midday. Same with locations: NH44 Singhu Border
has the most accidents (420), but Mumbai-Pune Expressway Khandala has the highest fatal share (33.8%). Resources should follow severity as well as volume.

**6. How strong is the alcohol finding, and how would you prove it statistically?**
Alcohol is in 6.5% of accidents but 29.7% of those are fatal versus 7.6% - about 3.9× higher. To test it properly I'd run a chi-square test of independence
on alcohol × severity, and a logistic regression to control for night-time and speed - that's in my future improvements. Correlation isn't causation:
alcohol is also more common at night, which is itself riskier.

**7. Does a higher speed limit cause more severe accidents?**
The data shows fatal share rising from 0.3% at 30 km/h to 41.1% at 120 km/h, but I'd be careful: speed limit is tied to road type (high limits are on
expressways), so it reflects the whole road environment, not just driver speed. I flagged that caveat in the insights file.

**8. How did you make sure your numbers are correct?**
I reconciled across tools: the same totals - 12,000 accidents, 19,839 casualties, 1,634 fatalities - appear in Pandas, MySQL and the Power BI cards.
I also added validation queries (unique IDs, date range, fatalities ≤ casualties) after loading the data.

**9. What would you do differently with real data?**
Add latitude/longitude for map hotspots, normalise accidents by traffic volume (so busy roads aren't unfairly "dangerous"), run significance tests,
and check data-quality differences between police stations or years.

**10. What recommendations would you give, and how do you prioritise them?**
I rank by impact and cost: (1) alcohol checks at night/weekends - big severity effect, low cost; (2) fix the highest-fatal-share expressway locations;
(3) weather alerts for fog/heavy rain - cheap; (4) resurface potholes - costly but broad; (5) heavy-vehicle controls. Each is tied to a specific finding.

**Bonus honesty point.** "Fatalities did not drop in 2020 even though accidents fell 28.6% (285 in 2019 vs 290 in 2020). In this data that comes from a few
mass-casualty crashes and a higher fatal share - it's a reminder that fatality counts are lumpy and need context."

---------------------------------------------------------------------------------------------------

## E. Python / Pandas questions (from this project)

| Question | Answer |
|---|---|
| How did you find missing values? | `df.isna().sum()`; show only columns with missing data. |
| How did you remove duplicates? | `df.duplicated().sum()` to count, `df.drop_duplicates()` to remove (keeps first). Also checked duplicates on `Accident_ID` because it is the primary key. |
| How did you standardise "Two Wheeler", "bike", "2-Wheeler"? | Strip + lower-case, then `.map()` with a dictionary to the official label; unmapped → "Other". |
| How did you convert dates? | `pd.to_datetime(format=..., errors="coerce")` once per format and `fillna` to combine, so pandas never guesses day/month order. |
| Why `errors="coerce"`? | Bad values become `NaT` instead of crashing; I count and handle them. |
| How did you fill missing age by group? | `df.groupby("Vehicle_Type")["Driver_Age"].transform("median")` returns a median for every row, so `fillna` can use it. |
| What is the difference between `loc` and `iloc`? | `loc` selects by label/condition (I used `df.loc[mask, col] = value`), `iloc` by integer position. |
| How did you create `Age_Group`? | `pd.cut(Driver_Age, bins=[17,24,34,49,64,120], labels=[...])`. |
| How did you build `Risk_Category`? | `np.select` with ordered conditions - first match wins - Critical, High, Medium, default Low. |
| `apply` vs vectorised? | Vectorised (`np.where`, `.str`, `groupby`) is faster; I used `apply` only for light-condition derivation on a few hundred rows. |
| `transform` vs `agg`? | `agg` returns one row per group; `transform` returns a value per original row. |
| `value_counts` vs `groupby().size()`? | Equivalent for counts; `value_counts` is sorted by default and shorter. |
| How did you build the Day × Hour heat-map? | `pivot_table(index="Day_of_Week", columns="Hour", values="Accident_ID", aggfunc="count")` then `sns.heatmap`. |
| What is `crosstab(normalize="index")`? | Row percentages - the share of Minor/Serious/Fatal inside each category (used for the 100% stacked charts). |
| Why `matplotlib.use("Agg")`? | Saves charts to files without opening windows - works on servers and in scripts. |
| Why is Pandas `SettingWithCopyWarning` a concern? | Modifying a slice may not change the original; I use `.copy()` and `.loc` assignment. |

## F. SQL questions (from this project's queries)

| Question | Answer |
|---|---|
| `WHERE` vs `HAVING`? | `WHERE` filters rows before grouping; `HAVING` filters groups after aggregation (e.g. `HAVING COUNT(*) >= 100` to drop small-sample locations). |
| How did you compute a percentage of total without a subquery? | `COUNT(*) / SUM(COUNT(*)) OVER ()` - a window function over the grouped result. |
| Why `SUM(Accident_Severity = 'Fatal')`? | In MySQL a true comparison equals 1, so summing counts the rows that match. |
| Explain your CASE pivot. | `SUM(CASE WHEN severity='Minor' THEN 1 ELSE 0 END)` turns severity rows into columns per weather type. |
| How did you calculate year-over-year change? | A CTE counts accidents per year, then `LAG(accidents) OVER (ORDER BY Year)` gets last year's value; change = (current − previous) / previous. |
| `RANK()` vs `ROW_NUMBER()` vs `DENSE_RANK()`? | `ROW_NUMBER` always unique; `RANK` gives ties the same rank and skips numbers; `DENSE_RANK` gives ties the same rank without gaps. |
| What does `PARTITION BY` do? | Restarts the window calculation for each group - e.g. rank locations separately inside each city (Q24). |
| What is a CTE and why use it? | `WITH name AS (...)` - a named temporary result that makes complex queries readable and reusable within one statement. |
| Why compare weekends per day? | Weekends have 2 days vs 5, so I divide by `COUNT(DISTINCT Accident_Date)` to get accidents per day. |
| How did you do the 3-month moving average? | `AVG(accidents) OVER (ORDER BY Year, Month_Num ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)`. |
| Why `NULLIF` in your queries? | `NULLIF(x, 0)` avoids divide-by-zero errors by returning NULL. |
| Which JOINs did you use and why? | A JOIN of location totals to city totals (share of city, Q26) and a CROSS JOIN to attach one overall average to every city (Q25). Single-table data means joins are only used on aggregated CTEs. |
| Why a primary key and indexes? | `Accident_ID` guarantees unique rows; indexes on Year, City, Location, Severity and Hour speed up the GROUP BY/WHERE columns. |
| How did you load the CSV? | `LOAD DATA LOCAL INFILE` with explicit column list and `STR_TO_DATE`; alternative: Python loader with SQLAlchemy `to_sql`. |
| How did you validate the import? | Row count = 12,000, unique IDs, min/max date, and a rule check (fatalities ≤ casualties = 0 violations). |
| Why `WITH ROLLUP`? | Adds a grand-total row (used in Q3 for the overall average). |

## G. Power BI / DAX questions

| Question | Answer |
|---|---|
| Measure vs calculated column? | A measure is computed at query time and reacts to slicers (KPIs, rates). A calculated column is computed per row at refresh (labels, sort keys). |
| Why a separate `_Measures` table? | Keeps measures organised and easy to find; no business meaning to the table itself. |
| What does `CALCULATE` do? | Evaluates an expression with modified filters, e.g. `CALCULATE([Total Accidents], Alcohol_Involved = "Yes")`. |
| Why `DIVIDE` instead of `/`? | Handles division by zero gracefully. |
| What is filter context? | The set of filters from slicers, chart axes and page/visual filters that a measure is evaluated under. |
| How did you get the month order right? | Sort `Month` by `Month_Num` (Column tools → Sort by column). |
| How did you build the Top-10 locations visual? | Visual-level Top N filter on `Location` by `[Fatalities per 100 Accidents]`, plus a filter of `[Total Accidents] ≥ 100` to avoid tiny samples. |
| How do slicers apply to all pages? | View → Sync slicers. |
| Why one fact table, no star schema? | The data is a single flat table; a Date table would be added if I needed time-intelligence like `SAMEPERIODLASTYEAR`. For year-over-year I used `MAX(Year) − 1` instead. |
| Import vs DirectQuery? | Import (data copied into the model, fast). DirectQuery queries MySQL live - useful for very large/live data. |
| How would you refresh it? | With the CSV/MySQL source updated, click Refresh in Desktop, or schedule refresh in Power BI Service via a gateway. |
| How did you keep colours consistent? | One theme JSON and fixed colours for Minor/Serious/Fatal on every chart. |

## H. Why each technology was used
* **Python + Pandas** - cleaning needs repeatable, documented logic; code can be re-run on new data and reviewed (unlike manual Excel edits).
* **NumPy** - fast conditional logic (`np.select`, `np.where`) and numeric handling for derived columns.
* **Matplotlib / Seaborn** - flexible static charts for analysis and the README; Seaborn adds heat-maps and cleaner defaults.
* **MySQL** - a shared, structured store; shows SQL, which almost every analyst job tests; queries are reusable by other teams.
* **Power BI** - interactive dashboards with slicers for non-technical users; reads CSV or MySQL; DAX for flexible KPIs.
* **CSV** - simple hand-off format between stages; opens in Excel for quick checks.

## I. Complete workflow, raw data → dashboard
1. **Generate / acquire** raw data (`generate_dataset.py` → `raw_accidents.csv`, 12,160 rows with deliberate dirt).
2. **Inspect** shape, types, missing values, duplicates, distinct spellings.
3. **Clean** (`data_cleaning.py`): drop duplicates → standardise text → parse dates/times → fix impossible values → handle missing values → flag outliers → derive features → save `cleaned_accidents.csv` and a cleaning report.
4. **Explore** (`exploratory_analysis.py`): 19 charts and computed insights (`key_insights.md`).
5. **Store** the cleaned data in MySQL (`accidents` table, primary key, indexes) and **validate** the load.
6. **Analyse with SQL**: 29 queries answering business questions.
7. **Visualise in Power BI**: connect → set types and sort orders → create DAX measures → build four pages with slicers → reconcile KPIs with SQL/Python.
8. **Communicate**: separate DATA FINDING from RECOMMENDATION and prioritise actions by impact and cost.

## Tips for the interview
* Lead with the **business question**, then the tools - not the reverse.
* Know two numbers by heart (e.g. 15.6% vs 6.9% night/midday fatal share; 3.9× alcohol) and tell one "frequency vs severity" story.
* Be ready to open the repo and show `data_cleaning.py` - explain two `DECISION:` comments in your own words.
* If you don't know something, say how you'd find out (e.g. "I'd test it with a chi-square test").
