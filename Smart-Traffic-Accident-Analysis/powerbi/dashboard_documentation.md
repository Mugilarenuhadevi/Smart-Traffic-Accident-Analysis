# Power BI Dashboard - Build Guide & Documentation

This guide tells you **exactly** what to click to rebuild the dashboard, which DAX measure goes where, and what each
page should show. Follow it top to bottom (about 2-3 hours the first time).

> Power BI Desktop is **Windows only** (free from the Microsoft Store). On Mac use a Windows VM or Power BI Service in the browser.

---------------------------------------------------------------------------------------------------

## 1. Connect to the data

### Option A - CSV (recommended, no database needed)
1. **Home -> Get data -> Text/CSV** -> choose `data/cleaned/cleaned_accidents.csv` -> **Transform Data**.
2. In Power Query check the column types (table below), then **Close & Apply**.
3. Rename the query/table to **`accidents`** (right-click the table in the Data pane -> Rename). All DAX below uses this name.

### Option B - MySQL
1. Install the *MySQL Connector/NET* (Power BI needs it), then **Get data -> MySQL database**.
   Server `localhost`, database `traffic_accident_db` -> select table `accidents`.
2. In Power Query **rename two columns** so the DAX below works for both options:
   `Accident_Date` -> `Date`, and `Accident_Time` -> `Time`.

### Column data types to verify in Power Query
| Column | Type | Column | Type |
|---|---|---|---|
| Accident_ID | Text | Number_of_Vehicles / Casualties / Fatalities | Whole number |
| Date | Date | Speed_Limit, Driver_Age, Hour, Day, Month_Num, Year | Whole number |
| Time | Time | Weekend_Flag, Mass_Casualty_Flag | Whole number |
| Casualty_Rate, Fatality_Rate | Decimal number | all other columns | Text |

> Tip: set **Year** to *Whole number* and its summarisation to **Don't summarize** (Column tools -> Summarization) so Power BI does not add the years together.

---------------------------------------------------------------------------------------------------

## 2. Prepare the model (sorting columns)
Text columns sort alphabetically (April before January). Fix that with *Sort by column*.

**a) Sort by an existing column** - select the column in the Data pane -> **Column tools -> Sort by column**:
| Column to sort | Sort by |
|---|---|
| `Month` | `Month_Num` |

**b) Create helper columns** - **Table tools -> New column** (select table `accidents` first). Paste each formula, then use *Sort by column* as shown.

```DAX
Day_of_Week_Num =
SWITCH ( accidents[Day_of_Week],
    "Monday", 1, "Tuesday", 2, "Wednesday", 3, "Thursday", 4, "Friday", 5, "Saturday", 6, "Sunday", 7 )
```
-> sort `Day_of_Week` by `Day_of_Week_Num`

```DAX
Severity_Order = SWITCH ( accidents[Accident_Severity], "Minor", 1, "Serious", 2, "Fatal", 3 )
```
-> sort `Accident_Severity` by `Severity_Order`

```DAX
Risk_Order = SWITCH ( accidents[Risk_Category], "Low", 1, "Medium", 2, "High", 3, "Critical", 4 )
```
-> sort `Risk_Category` by `Risk_Order`

```DAX
Time_Period_Order =
SWITCH ( accidents[Time_Period],
    "Late Night (12-4 AM)", 1, "Early Morning (5-7 AM)", 2, "Morning Peak (8-10 AM)", 3,
    "Midday (11 AM-3 PM)", 4, "Evening Peak (4-8 PM)", 5, "Night (9-11 PM)", 6 )
```
-> sort `Time_Period` by `Time_Period_Order`

```DAX
Speed_Limit_Label = accidents[Speed_Limit] & " km/h"
```
-> sort `Speed_Limit_Label` by `Speed_Limit`   (makes the speed axis categorical instead of continuous)

---------------------------------------------------------------------------------------------------

## 3. DAX measures
**Where to create them:** Home -> **Enter data** -> leave the grid empty, name the table **`_Measures`** -> Load.
Then select `_Measures` in the Data pane -> **Table tools -> New measure** and paste each formula one at a time.
(Putting measures in their own table keeps the model tidy - a good-practice point to mention in interviews.)

**Measures vs calculated columns:** a *measure* is calculated on the fly and reacts to slicers (use for KPIs and rates).
A *calculated column* is calculated once per row when data loads (use for labels / sorting).

### 3.1 Core KPIs
```DAX
Total Accidents = COUNTROWS ( accidents )

Total Casualties = SUM ( accidents[Number_of_Casualties] )

Total Fatalities = SUM ( accidents[Number_of_Fatalities] )

Fatality Rate = DIVIDE ( [Total Fatalities], [Total Casualties], 0 )          -- format as % (deaths / casualties)

Average Casualties = DIVIDE ( [Total Casualties], [Total Accidents], 0 )       -- format: 2 decimals
```
`DIVIDE` returns the 3rd argument (0) instead of an error when the denominator is zero.

### 3.2 Severity
```DAX
Severe Accident Count =
CALCULATE ( [Total Accidents], accidents[Accident_Severity] IN { "Serious", "Fatal" } )

Fatal Accident Count =
CALCULATE ( [Total Accidents], accidents[Accident_Severity] = "Fatal" )

Severe Accident % = DIVIDE ( [Severe Accident Count], [Total Accidents], 0 )   -- format %

Fatal Accident % = DIVIDE ( [Fatal Accident Count], [Total Accidents], 0 )      -- format %

Fatalities per 100 Accidents = DIVIDE ( [Total Fatalities], [Total Accidents], 0 ) * 100

Critical Accidents =
CALCULATE ( [Total Accidents], accidents[Risk_Category] = "Critical" )
```

### 3.3 Alcohol and weekend
```DAX
Alcohol Related Accidents =
CALCULATE ( [Total Accidents], accidents[Alcohol_Involved] = "Yes" )

Alcohol % (known) =
DIVIDE (
    [Alcohol Related Accidents],
    CALCULATE ( [Total Accidents], accidents[Alcohol_Involved] IN { "Yes", "No" } ),   -- ignore 'Unknown'
    0 )

Weekend Accidents =
CALCULATE ( [Total Accidents], accidents[Weekend_Flag] = 1 )

Weekday Accidents =
CALCULATE ( [Total Accidents], accidents[Weekend_Flag] = 0 )
```

### 3.4 Trend
```DAX
Accidents Previous Year =
CALCULATE ( [Total Accidents], accidents[Year] = MAX ( accidents[Year] ) - 1 )

YoY Change % =
VAR Prev = [Accidents Previous Year]
RETURN IF ( Prev = 0, BLANK (), DIVIDE ( [Total Accidents] - Prev, Prev ) )          -- format %
```

### 3.5 Dynamic "answer" measures for the Insights page (used inside Card visuals)
```DAX
Peak Hour =
VAR T = ADDCOLUMNS ( VALUES ( accidents[Hour] ), "n", [Total Accidents] )
RETURN FORMAT ( MAXX ( TOPN ( 1, T, [n], DESC ), accidents[Hour] ), "00" ) & ":00"

Busiest Day =
VAR T = ADDCOLUMNS ( VALUES ( accidents[Day_of_Week] ), "n", [Total Accidents] )
RETURN MAXX ( TOPN ( 1, T, [n], DESC ), accidents[Day_of_Week] )

Most Dangerous Weather =
VAR T = ADDCOLUMNS (
            FILTER ( VALUES ( accidents[Weather_Condition] ), accidents[Weather_Condition] <> "Unknown" ),
            "r", [Severe Accident %] )
RETURN MAXX ( TOPN ( 1, T, [r], DESC ), accidents[Weather_Condition] )

Alcohol Risk Multiple =
DIVIDE (
    CALCULATE ( [Fatal Accident %], accidents[Alcohol_Involved] = "Yes" ),
    CALCULATE ( [Fatal Accident %], accidents[Alcohol_Involved] = "No" ) )                -- format: 0.0"x"
```

---------------------------------------------------------------------------------------------------

## 4. Look & feel
* **View -> Themes -> Browse for themes** -> choose `powerbi/accident_theme.json` (blue / amber / red / green palette).
* Canvas: 16:9 (default). Page background light grey `#F3F4F6`; visuals white with a thin border and rounded corners.
* **Severity colours - keep them identical on every chart:** Minor `#2E9E6B` (green), Serious `#F2A33A` (amber), Fatal `#C8372D` (red).
  Set them once per chart: *Format -> Visuals -> Columns (or Slices) -> Colors*.
* Page header: a text box with the page title + a thin coloured shape. Add data labels on every bar chart.

---------------------------------------------------------------------------------------------------

## 5. Pages

### PAGE 1 - EXECUTIVE OVERVIEW
| # | Visual | Type | Fields |
|---|---|---|---|
| 1 | Total Accidents | Card | `[Total Accidents]` |
| 2 | Total Fatalities | Card | `[Total Fatalities]` |
| 3 | Total Casualties | Card | `[Total Casualties]` |
| 4 | Fatality Rate | Card | `[Fatality Rate]` (format %) |
| 5 | Avg Casualties / Accident | Card | `[Average Casualties]` |
| 6 | Accidents by Year | Column chart (or line) | X `Year` - Y `[Total Accidents]` (add `[YoY Change %]` as tooltip) |
| 7 | Accidents by Month | Column chart | X `Month` (sorted by Month_Num) - Y `[Total Accidents]` |
| 8 | Severity Distribution | Donut chart | Legend `Accident_Severity` - Values `[Total Accidents]` |
| 9 | Accidents by Weather | Bar chart | Y `Weather_Condition` - X `[Total Accidents]` |
| 10 | Accidents by Road Condition | Bar chart | Y `Road_Condition` - X `[Total Accidents]` |

Layout: 5 KPI cards in one row on top; row 2 = Year + Month + Severity donut; row 3 = Weather + Road Condition.
Slicer panel on the left or top (see section 6).

### PAGE 2 - RISK ANALYSIS
| # | Visual | Type | Fields |
|---|---|---|---|
| 1 | Accidents by Hour | Line chart (area) | X `Hour` - Y `[Total Accidents]` |
| 2 | Day-of-week x Hour heat-map | Matrix | Rows `Day_of_Week` - Columns `Hour` - Values `[Total Accidents]` -> Format -> *Cell elements -> Background colour (gradient)* |
| 3 | Accidents by Day of Week | Column chart | X `Day_of_Week` - Y `[Total Accidents]` |
| 4 | Weekend vs Weekday | Donut or clustered column | Legend/X `Day_Type` - Values `[Total Accidents]`; add a small table with `Day_Type`, `[Total Accidents]`, `[Fatal Accident %]` |
| 5 | Speed Limit vs Severity | 100% stacked column | X `Speed_Limit_Label` - Legend `Accident_Severity` - Values `[Total Accidents]` |
| 6 | Alcohol Involvement | Two visuals: Donut (`Alcohol_Involved`, `[Total Accidents]`) + 100% stacked bar (`Alcohol_Involved` vs `Accident_Severity`). Add visual-level filter `Alcohol_Involved` is not `Unknown` |
| 7 | Light Condition vs Severity | 100% stacked column | X `Light_Condition` - Legend `Accident_Severity` - Values `[Total Accidents]` |

### PAGE 3 - LOCATION & VEHICLE ANALYSIS
| # | Visual | Type | Fields / Filter |
|---|---|---|---|
| 1 | **Top 10 High-Risk Locations** | Bar chart | Y `Location` - X `[Fatalities per 100 Accidents]`. Filters pane -> Location -> *Top N* = 10 **By value** `[Fatalities per 100 Accidents]`. Add a 2nd visual-level filter `[Total Accidents]` >= 100 so tiny samples are excluded. Tooltip: `[Total Accidents]`, `[Total Fatalities]` |
| 2 | Accidents by City | Bar chart (or filled map) | Y `City` - X `[Total Accidents]` |
| 3 | Accidents by Vehicle Type | Bar chart | Y `Vehicle_Type` - X `[Total Accidents]` |
| 4 | Fatalities by Location | Bar chart | Y `Location` - X `[Total Fatalities]` - Top N 10 |
| 5 | Severity by Vehicle Type | 100% stacked bar | Y `Vehicle_Type` - Legend `Accident_Severity` - Values `[Total Accidents]` |
| 6 | Detail table (optional) | Table | `Location`, `City`, `[Total Accidents]`, `[Total Fatalities]`, `[Fatal Accident %]` - turn on conditional formatting (data bars) |

Add a **drill-through** (optional but impressive): create a page "Location Detail", drag `Location` into *Drill through*; then right-clicking a location on Page 3 opens its detail.

### PAGE 4 - INSIGHTS
Build a clean "executive summary" page:
* Top row: 4 Card visuals using the dynamic measures - `[Peak Hour]`, `[Busiest Day]`, `[Most Dangerous Weather]`, `[Alcohol Risk Multiple]`.
* Below: text boxes (Insert -> Text box), one per theme, each with **Finding** and **Recommendation** in two colours
  (finding = dark text, recommendation = blue text). Use the findings below (they were calculated from the dataset
  in this repo by `python/exploratory_analysis.py`; re-check them if you regenerate the data).

| Theme | DATA FINDING | RECOMMENDATION |
|---|---|---|
| Time | Accidents peak at 18:00 (965), 19:00 (925) and 17:00 (760). Late-night (12-4 AM) accidents are fewer but 15.6% are fatal vs 6.9% at midday. | Deploy traffic police/ambulances for the 5-8 PM peak; add night-time speed and drink-driving checks. |
| Weather | Fog (52.4%) and heavy rain (50.2%) have the highest severe-accident share vs 35.1% in clear weather. | Weather alerts, variable speed limits and fog lights on affected corridors. |
| Road | Severe share: wet 45.2%, damaged 44.2%, dry 35.0%. | Resurface potholes, improve drainage/anti-skid surfacing, mark construction zones. |
| Vehicles | Two-wheelers are 34.3% of accidents; trucks (14.6%) and buses (12.6%) have the highest fatal share. | Helmet drives for riders; speed limiters and fatigue rules for heavy vehicles. |
| Locations | Mumbai-Pune Expressway Khandala (33.8%), Yamuna Expressway Entry (28.9%) and Nehru Outer Ring Exit 12 (28.3%) have the highest fatal share; NH44 Singhu Border has the most accidents (420). | Cameras, lighting and emergency points at the highest fatal-share locations first. |
| Alcohol | 29.7% of alcohol-related accidents are fatal vs 7.6% otherwise (3.9x). Alcohol share is 17.2% at 9 PM-4 AM vs 4.3% by day. | Night/weekend breathalyser checkpoints; awareness campaigns. |
| Weekend | 7.0 accidents/day on weekends vs 6.4 on weekdays; alcohol share 8.8% vs 5.5%. | Extra weekend-night patrols and trauma staffing. |
| Speed / light | Fatal share climbs from 0.3% (30 km/h) to 41.1% (120 km/h). Unlit darkness: 22.0% fatal vs 7.1% in daylight. | Average-speed cameras; fix unlit road stretches. |

*Caveat to mention on the page:* the speed limit is linked to road type (high limits are on expressways/highways), so it shows risk of the road environment, not only driver speed.

---------------------------------------------------------------------------------------------------

## 6. Slicers (on every page)
Insert -> **Slicer** (one per field) and place them in the same position on each page:
| Slicer | Field | Style |
|---|---|---|
| Year | `Year` | Tile / between (slider) |
| City | `City` | Dropdown |
| Accident Severity | `Accident_Severity` | Tile buttons |
| Weather Condition | `Weather_Condition` | Dropdown |
| Road Condition | `Road_Condition` | Dropdown |
| Vehicle Type | `Vehicle_Type` | Dropdown |

**Sync slicers across pages:** View -> **Sync slicers** -> tick *Sync* and *Visible* for the pages you want.
Add a **Clear all slicers** bookmark button (Insert -> Buttons -> Clear all slicers) for a polished look.

**Page navigation:** Insert -> Buttons -> Navigator -> Page navigator (gives clickable page tabs automatically).

---------------------------------------------------------------------------------------------------

## 7. Check your work (reconcile with SQL / Python)
With **no slicers selected**, your Page 1 cards must equal:
| KPI | Expected value |
|---|---|
| Total Accidents | 12,000 |
| Total Casualties | 19,839 |
| Total Fatalities | 1,634 |
| Fatality Rate | 8.24% |
| Average Casualties | 1.65 |

If they match SQL Query Q1-Q3 and the Python output, your data model is correct. (Matching numbers across tools is something interviewers like to hear.)

## 8. Save & share
* Save as `powerbi/Traffic_Accident_Dashboard.pbix`.
* Take screenshots of each page (Windows+Shift+S) and save in `visualizations/powerbi_*.png`; reference them in the README.
* Optional: **File -> Export -> PDF**, or **Publish** to Power BI Service and use *File -> Embed report -> Publish to web* (public link for your resume - only for non-sensitive data like this one).
