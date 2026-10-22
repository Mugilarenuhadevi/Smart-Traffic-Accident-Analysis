/* =====================================================================================
   SMART TRAFFIC ACCIDENT RISK ANALYSIS  -  MySQL 8.0+
   File : sql/accident_analysis.sql

   HOW TO USE (MySQL Workbench):
     1. Run PART 1 (create database + table).
     2. Run PART 2 (load the CSV)  - OR use  python python/load_to_mysql.py  instead.
     3. Run PART 3 (validation) to confirm 12,000 rows were loaded.
     4. Run the queries in PART 4 ONE AT A TIME (select a query -> Ctrl+Enter).

   Definitions used in the queries
     Severe accident  = Accident_Severity IN ('Serious','Fatal')   i.e. <> 'Minor'
     Fatal %          = share of accidents classified 'Fatal'
     Fatality rate    = fatalities per 100 casualties
   MySQL trick:  SUM(condition) counts the rows where the condition is TRUE (TRUE = 1).
   ===================================================================================== */


/* =====================================================================================
   PART 1 - DATABASE & TABLE
   ===================================================================================== */
CREATE DATABASE IF NOT EXISTS traffic_accident_db
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE traffic_accident_db;

DROP TABLE IF EXISTS accidents;

CREATE TABLE accidents (
    Accident_ID          VARCHAR(12)   NOT NULL,          -- e.g. ACC-000001
    Accident_Date        DATE          NOT NULL,
    Accident_Time        TIME          NOT NULL,
    Hour                 TINYINT       NOT NULL,          -- 0-23
    Day                  TINYINT       NOT NULL,          -- day of month
    Day_of_Week          VARCHAR(10)   NOT NULL,
    Month_Num            TINYINT       NOT NULL,
    Month                VARCHAR(10)   NOT NULL,
    Year                 SMALLINT      NOT NULL,
    Weekend_Flag         TINYINT       NOT NULL,          -- 1 = Sat/Sun
    Day_Type             VARCHAR(8)    NOT NULL,          -- Weekday / Weekend
    Time_Period          VARCHAR(30)   NOT NULL,
    Location             VARCHAR(60)   NOT NULL,
    City                 VARCHAR(30)   NOT NULL,
    State                VARCHAR(30)   NOT NULL,
    Weather_Condition    VARCHAR(20)   NOT NULL,
    Road_Condition       VARCHAR(25)   NOT NULL,
    Road_Type            VARCHAR(20)   NOT NULL,
    Vehicle_Type         VARCHAR(20)   NOT NULL,
    Number_of_Vehicles   TINYINT       NOT NULL,
    Number_of_Casualties SMALLINT      NOT NULL,
    Number_of_Fatalities SMALLINT      NOT NULL,
    Accident_Severity    VARCHAR(10)   NOT NULL,          -- Minor / Serious / Fatal
    Speed_Limit          SMALLINT      NOT NULL,
    Light_Condition      VARCHAR(30)   NOT NULL,
    Alcohol_Involved     VARCHAR(10)   NOT NULL,          -- Yes / No / Unknown
    Driver_Age           TINYINT UNSIGNED NOT NULL,
    Age_Group            VARCHAR(10)   NOT NULL,
    Driver_Gender        VARCHAR(10)   NOT NULL,
    Casualty_Rate        DECIMAL(6,2)  NOT NULL,          -- casualties per vehicle
    Fatality_Rate        DECIMAL(6,2)  NOT NULL,          -- % of casualties who died
    Risk_Category        VARCHAR(10)   NOT NULL,          -- Low / Medium / High / Critical
    Mass_Casualty_Flag   TINYINT       NOT NULL,
    PRIMARY KEY (Accident_ID),
    -- indexes speed up the GROUP BY / WHERE columns we use the most
    INDEX idx_year     (Year),
    INDEX idx_city     (City),
    INDEX idx_location (Location),
    INDEX idx_severity (Accident_Severity),
    INDEX idx_hour     (Hour)
) ENGINE = InnoDB;


/* =====================================================================================
   PART 2 - IMPORT THE CLEANED CSV
   -------------------------------------------------------------------------------------
   OPTION A (this script): LOAD DATA LOCAL INFILE
       * Change the path below to YOUR absolute path. Use forward slashes even on Windows.
       * Local-infile must be enabled on BOTH sides. If you get "Error 3948 / 2068":
             SET GLOBAL local_infile = 1;
         and in Workbench: Connection -> Advanced -> "Others" box ->  OPT_LOCAL_INFILE=1
   OPTION B: python python/load_to_mysql.py        (easiest - no MySQL settings needed)
   OPTION C: Workbench -> right-click table 'accidents' -> Table Data Import Wizard
   ===================================================================================== */
LOAD DATA LOCAL INFILE 'C:/Smart-Traffic-Accident-Analysis/data/cleaned/cleaned_accidents.csv'
INTO TABLE accidents
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(Accident_ID, @csv_date, @csv_time, Hour, Day, Day_of_Week, Month_Num, Month, Year, Weekend_Flag, Day_Type,
 Time_Period, Location, City, State, Weather_Condition, Road_Condition, Road_Type, Vehicle_Type,
 Number_of_Vehicles, Number_of_Casualties, Number_of_Fatalities, Accident_Severity, Speed_Limit,
 Light_Condition, Alcohol_Involved, Driver_Age, Age_Group, Driver_Gender, Casualty_Rate, Fatality_Rate,
 Risk_Category, Mass_Casualty_Flag)
SET Accident_Date = STR_TO_DATE(@csv_date, '%Y-%m-%d'),
    Accident_Time = @csv_time;


/* =====================================================================================
   PART 3 - VALIDATION (always check after an import!)
   ===================================================================================== */
-- Expect 12000 rows and 0 duplicate IDs
SELECT COUNT(*) AS total_rows, COUNT(DISTINCT Accident_ID) AS unique_ids FROM accidents;

-- Expect min 2019-01-01 and max 2023-12-31
SELECT MIN(Accident_Date) AS first_date, MAX(Accident_Date) AS last_date FROM accidents;

-- Business-rule check: casualties must never be below fatalities (expect 0)
SELECT COUNT(*) AS rule_violations FROM accidents WHERE Number_of_Fatalities > Number_of_Casualties;


/* =====================================================================================
   PART 4 - BUSINESS ANALYSIS QUERIES
   ===================================================================================== */

/* -------------------------------------------------------------------------------------
   Q1. TOTAL NUMBER OF ACCIDENTS
   QUESTION : How big is the problem?
   WHAT IT DOES: COUNT(*) counts every row; each row is one accident.
   LOOK FOR : The headline KPI - same number as the Power BI "Total Accidents" card.
   ------------------------------------------------------------------------------------- */
SELECT COUNT(*) AS total_accidents
FROM accidents;


/* -------------------------------------------------------------------------------------
   Q2. TOTAL CASUALTIES, FATALITIES AND OVERALL FATALITY RATE
   QUESTION : How many people were hurt or killed, and what share died?
   WHAT IT DOES: SUM adds the people columns; fatality rate = deaths / casualties x 100.
   LOOK FOR : Casualties INCLUDE fatalities, so the rate is "deaths per 100 people harmed".
   ------------------------------------------------------------------------------------- */
SELECT SUM(Number_of_Casualties)                                             AS total_casualties,
       SUM(Number_of_Fatalities)                                             AS total_fatalities,
       ROUND(100 * SUM(Number_of_Fatalities) / SUM(Number_of_Casualties), 2) AS fatality_rate_pct
FROM accidents;


/* -------------------------------------------------------------------------------------
   Q3. AVERAGE CASUALTIES PER ACCIDENT (overall + by severity)
   QUESTION : How many people does a typical accident harm?
   WHAT IT DOES: AVG per severity, plus MAX / MIN. WITH ROLLUP adds an 'ALL' total row.
   LOOK FOR : Fatal accidents should harm more people on average. A big MAX shows a
              mass-casualty event (the outliers we flagged in cleaning).
   ------------------------------------------------------------------------------------- */
SELECT COALESCE(Accident_Severity, 'ALL ACCIDENTS')   AS severity,
       COUNT(*)                                        AS accidents,
       ROUND(AVG(Number_of_Casualties), 2)             AS avg_casualties,
       MIN(Number_of_Casualties)                       AS min_casualties,
       MAX(Number_of_Casualties)                       AS max_casualties
FROM accidents
GROUP BY Accident_Severity WITH ROLLUP;


/* -------------------------------------------------------------------------------------
   Q4. ACCIDENT SEVERITY DISTRIBUTION
   QUESTION : What share of accidents are Minor, Serious or Fatal?
   WHAT IT DOES: Counts per severity; the WINDOW function SUM(COUNT(*)) OVER () gives the grand
                 total on every row so we can compute a percentage without a subquery.
   LOOK FOR : The fatal share - every percentage point is lives lost.
   ------------------------------------------------------------------------------------- */
SELECT Accident_Severity,
       COUNT(*)                                          AS accidents,
       ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)  AS pct_of_total
FROM accidents
GROUP BY Accident_Severity
ORDER BY FIELD(Accident_Severity, 'Minor', 'Serious', 'Fatal');


/* -------------------------------------------------------------------------------------
   Q5. ACCIDENTS BY YEAR WITH YEAR-OVER-YEAR CHANGE   (CTE + LAG window function)
   QUESTION : Are accidents increasing or decreasing?
   WHAT IT DOES: The CTE counts accidents per year (+ casualties/fatalities); LAG() reads the previous
                 year's value so we can calculate % change.
   LOOK FOR : A sharp dip in 2020 (lockdown) followed by recovery; whether recent years exceed 2019.
   ------------------------------------------------------------------------------------- */
WITH yearly AS (
    SELECT Year, COUNT(*) AS accidents,
           SUM(Number_of_Casualties) AS casualties,
           SUM(Number_of_Fatalities) AS fatalities
    FROM accidents
    GROUP BY Year
)
SELECT Year, accidents, casualties, fatalities,
       LAG(accidents) OVER (ORDER BY Year)                                   AS prev_year_accidents,
       ROUND(100 * (accidents - LAG(accidents) OVER (ORDER BY Year))
                 / LAG(accidents) OVER (ORDER BY Year), 1)                   AS yoy_change_pct
FROM yearly
ORDER BY Year;


/* -------------------------------------------------------------------------------------
   Q6. ACCIDENTS BY MONTH (seasonality)
   QUESTION : Which months are the busiest?
   WHAT IT DOES: Groups by Month_Num (so the output sorts January -> December, not alphabetically)
                 and shows average accidents per year for that month.
   LOOK FOR : Monsoon months (Jun-Sep) and the festive/winter-fog months (Oct-Jan).
   ------------------------------------------------------------------------------------- */
SELECT Month_Num, Month,
       COUNT(*)                                  AS accidents,
       ROUND(COUNT(*) / COUNT(DISTINCT Year), 0) AS avg_per_year,
       SUM(Number_of_Fatalities)                 AS fatalities
FROM accidents
GROUP BY Month_Num, Month
ORDER BY Month_Num;


/* -------------------------------------------------------------------------------------
   Q7. ACCIDENTS BY DAY OF WEEK
   QUESTION : Which weekdays are the most dangerous?
   WHAT IT DOES: FIELD() forces Monday-Sunday order; also shows the fatal % per day.
   LOOK FOR : Whether Friday/Saturday have both higher volume and a higher fatal share.
   ------------------------------------------------------------------------------------- */
SELECT Day_of_Week,
       COUNT(*)                                                   AS accidents,
       ROUND(100 * SUM(Accident_Severity = 'Fatal') / COUNT(*), 1) AS fatal_pct
FROM accidents
GROUP BY Day_of_Week
ORDER BY FIELD(Day_of_Week, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday');


/* -------------------------------------------------------------------------------------
   Q8. ACCIDENTS BY HOUR OF DAY
   QUESTION : At what time of day do accidents happen?
   WHAT IT DOES: Counts per hour and the share of all accidents; RANK() marks the top hours.
   LOOK FOR : Evening rush-hour peak, and quiet hours that still show a high fatal %.
   ------------------------------------------------------------------------------------- */
SELECT Hour,
       COUNT(*)                                                    AS accidents,
       ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)            AS pct_of_all,
       ROUND(100 * SUM(Accident_Severity = 'Fatal') / COUNT(*), 1) AS fatal_pct,
       RANK() OVER (ORDER BY COUNT(*) DESC)                        AS volume_rank
FROM accidents
GROUP BY Hour
ORDER BY Hour;


/* -------------------------------------------------------------------------------------
   Q9. TIME PERIOD vs SEVERITY (peak volume is not the same as peak danger)
   QUESTION : Which part of the day is the deadliest, not just the busiest?
   WHAT IT DOES: Uses the Time_Period column created in Python; compares volume to severe % and
                 fatal %.
   LOOK FOR : A period with FEW accidents but a HIGH fatal % (late night) - that is where
              enforcement gives the best return.
   ------------------------------------------------------------------------------------- */
SELECT Time_Period,
       COUNT(*)                                                      AS accidents,
       ROUND(100 * SUM(Accident_Severity <> 'Minor') / COUNT(*), 1)  AS severe_pct,
       ROUND(100 * SUM(Accident_Severity = 'Fatal') / COUNT(*), 1)   AS fatal_pct,
       ROUND(100 * SUM(Alcohol_Involved = 'Yes')
                 / NULLIF(SUM(Alcohol_Involved <> 'Unknown'), 0), 1) AS alcohol_pct
FROM accidents
GROUP BY Time_Period
ORDER BY fatal_pct DESC;


/* -------------------------------------------------------------------------------------
   Q10. TOP 10 HIGH-RISK LOCATIONS
   QUESTION : Which locations should the authorities fix first?
   WHAT IT DOES: Per location: accidents, casualties, fatalities, fatal %. HAVING removes
                 locations with too few accidents to be reliable. Ordered by fatalities.
   LOOK FOR : Locations that appear at the top for BOTH volume and fatal % are priority #1.
   ------------------------------------------------------------------------------------- */
SELECT Location, City,
       COUNT(*)                                                    AS accidents,
       SUM(Number_of_Casualties)                                   AS casualties,
       SUM(Number_of_Fatalities)                                   AS fatalities,
       ROUND(100 * SUM(Accident_Severity = 'Fatal') / COUNT(*), 1) AS fatal_pct
FROM accidents
GROUP BY Location, City
HAVING COUNT(*) >= 100
ORDER BY fatalities DESC, accidents DESC
LIMIT 10;


/* -------------------------------------------------------------------------------------
   Q11. MOST COMMON WEATHER CONDITIONS AT THE TIME OF ACCIDENTS
   QUESTION : In which weather do most accidents happen?
   WHAT IT DOES: Counts and share per weather type.
   LOOK FOR : Do NOT conclude "clear weather is dangerous" - most days are clear. Compare with Q12,
              which looks at severity, and remember 'Unknown' means weather was not recorded.
   ------------------------------------------------------------------------------------- */
SELECT Weather_Condition,
       COUNT(*)                                          AS accidents,
       ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)  AS pct_of_total
FROM accidents
GROUP BY Weather_Condition
ORDER BY accidents DESC;


/* -------------------------------------------------------------------------------------
   Q12. SEVERITY BY WEATHER  (CASE-based pivot table)
   QUESTION : Which weather produces the most SEVERE accidents?
   WHAT IT DOES: SUM(CASE WHEN ...) turns the severity rows into three columns (a pivot) and
                 calculates the % of each severity inside every weather type.
   LOOK FOR : Weather types whose Fatal % and Severe % are well above the 'Clear' row.
   ------------------------------------------------------------------------------------- */
SELECT Weather_Condition,
       COUNT(*)                                                               AS accidents,
       SUM(CASE WHEN Accident_Severity = 'Minor'   THEN 1 ELSE 0 END)         AS minor,
       SUM(CASE WHEN Accident_Severity = 'Serious' THEN 1 ELSE 0 END)         AS serious,
       SUM(CASE WHEN Accident_Severity = 'Fatal'   THEN 1 ELSE 0 END)         AS fatal,
       ROUND(100 * SUM(Accident_Severity <> 'Minor') / COUNT(*), 1)           AS severe_pct,
       ROUND(100 * SUM(Accident_Severity = 'Fatal')  / COUNT(*), 1)           AS fatal_pct
FROM accidents
WHERE Weather_Condition <> 'Unknown'
GROUP BY Weather_Condition
ORDER BY severe_pct DESC;


/* -------------------------------------------------------------------------------------
   Q13. MOST DANGEROUS ROAD CONDITIONS
   QUESTION : Which road surfaces lead to the worst outcomes?
   WHAT IT DOES: Volume, average casualties, severe % and fatality rate by road condition.
   LOOK FOR : The gap between 'Dry' and Wet / Damaged roads.
   ------------------------------------------------------------------------------------- */
SELECT Road_Condition,
       COUNT(*)                                                         AS accidents,
       ROUND(AVG(Number_of_Casualties), 2)                              AS avg_casualties,
       ROUND(100 * SUM(Accident_Severity <> 'Minor') / COUNT(*), 1)     AS severe_pct,
       ROUND(100 * SUM(Number_of_Fatalities) / SUM(Number_of_Casualties), 2) AS fatality_rate_pct
FROM accidents
WHERE Road_Condition <> 'Unknown'
GROUP BY Road_Condition
ORDER BY severe_pct DESC;


/* -------------------------------------------------------------------------------------
   Q14. SEVERITY BY ROAD CONDITION (full severity split, pivot)
   QUESTION : How is each road condition split between Minor / Serious / Fatal?
   WHAT IT DOES: Same pivot technique as Q12, on road condition and road type together.
   LOOK FOR : Which road type + condition pairs have the highest fatal %.
   ------------------------------------------------------------------------------------- */
SELECT Road_Type, Road_Condition,
       COUNT(*)                                                       AS accidents,
       ROUND(100 * SUM(Accident_Severity = 'Minor')   / COUNT(*), 1)  AS minor_pct,
       ROUND(100 * SUM(Accident_Severity = 'Serious') / COUNT(*), 1)  AS serious_pct,
       ROUND(100 * SUM(Accident_Severity = 'Fatal')   / COUNT(*), 1)  AS fatal_pct
FROM accidents
WHERE Road_Condition <> 'Unknown'
GROUP BY Road_Type, Road_Condition
HAVING COUNT(*) >= 30
ORDER BY fatal_pct DESC;


/* -------------------------------------------------------------------------------------
   Q15. VEHICLE TYPE ANALYSIS
   QUESTION : Which vehicles are most involved - and which are most deadly?
   WHAT IT DOES: Share of accidents, casualties, fatalities, fatal % and average vehicles involved.
   LOOK FOR : A vehicle can be #1 in COUNT but not in fatal %. Trucks/buses are rarer but deadlier.
   ------------------------------------------------------------------------------------- */
SELECT Vehicle_Type,
       COUNT(*)                                                    AS accidents,
       ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)            AS pct_of_accidents,
       SUM(Number_of_Casualties)                                   AS casualties,
       SUM(Number_of_Fatalities)                                   AS fatalities,
       ROUND(100 * SUM(Accident_Severity = 'Fatal') / COUNT(*), 1) AS fatal_pct,
       ROUND(AVG(Number_of_Vehicles), 2)                           AS avg_vehicles_involved
FROM accidents
GROUP BY Vehicle_Type
ORDER BY accidents DESC;


/* -------------------------------------------------------------------------------------
   Q16. ALCOHOL-RELATED ACCIDENTS
   QUESTION : How much deadlier are accidents involving alcohol?
   WHAT IT DOES: Compares Yes vs No (Unknown excluded to keep the comparison fair).
   LOOK FOR : The ratio of Fatal % for 'Yes' vs 'No'.
   ------------------------------------------------------------------------------------- */
SELECT Alcohol_Involved,
       COUNT(*)                                                        AS accidents,
       ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)                AS pct_of_known,
       ROUND(AVG(Number_of_Casualties), 2)                             AS avg_casualties,
       ROUND(100 * SUM(Accident_Severity = 'Fatal') / COUNT(*), 1)     AS fatal_pct,
       SUM(Number_of_Fatalities)                                       AS fatalities
FROM accidents
WHERE Alcohol_Involved IN ('Yes', 'No')
GROUP BY Alcohol_Involved;


/* -------------------------------------------------------------------------------------
   Q17. WHEN DOES ALCOHOL-RELATED DRIVING HAPPEN?
   QUESTION : At what time and on which type of day is alcohol involved most often?
   WHAT IT DOES: Percentage of accidents with alcohol for every Time_Period x Day_Type combination.
   LOOK FOR : Highest percentages -> best times for breathalyser checkpoints.
   ------------------------------------------------------------------------------------- */
SELECT Time_Period, Day_Type,
       COUNT(*)                                                   AS accidents,
       SUM(Alcohol_Involved = 'Yes')                              AS alcohol_accidents,
       ROUND(100 * SUM(Alcohol_Involved = 'Yes') / COUNT(*), 1)   AS alcohol_pct
FROM accidents
WHERE Alcohol_Involved IN ('Yes', 'No')
GROUP BY Time_Period, Day_Type
ORDER BY alcohol_pct DESC;


/* -------------------------------------------------------------------------------------
   Q18. WEEKEND vs WEEKDAY ACCIDENTS (fair comparison)
   QUESTION : Is the weekend really worse?
   WHAT IT DOES: A weekend has only 2 days and a week has 5 weekdays, so raw totals are unfair.
                 We divide by the number of distinct calendar days -> accidents PER DAY.
   LOOK FOR : Accidents per day, fatal % and alcohol % side by side.
   ------------------------------------------------------------------------------------- */
SELECT Day_Type,
       COUNT(*)                                                         AS accidents,
       COUNT(DISTINCT Accident_Date)                                    AS calendar_days,
       ROUND(COUNT(*) / COUNT(DISTINCT Accident_Date), 2)               AS accidents_per_day,
       ROUND(100 * SUM(Accident_Severity <> 'Minor') / COUNT(*), 1)     AS severe_pct,
       ROUND(100 * SUM(Accident_Severity = 'Fatal') / COUNT(*), 1)      AS fatal_pct,
       ROUND(100 * SUM(Alcohol_Involved = 'Yes')
                 / NULLIF(SUM(Alcohol_Involved <> 'Unknown'), 0), 1)    AS alcohol_pct
FROM accidents
GROUP BY Day_Type;


/* -------------------------------------------------------------------------------------
   Q19. FATALITY RATE BY LOCATION
   QUESTION : Which locations are most deadly per accident (not just busiest)?
   WHAT IT DOES: Fatalities per 100 accidents and per 100 casualties. HAVING >= 100 accidents
                 avoids misleading rates from tiny samples.
   LOOK FOR : Locations on this list that were NOT in the Q10 volume list - hidden danger spots.
   ------------------------------------------------------------------------------------- */
SELECT Location, City, Road_Type_Main,
       accidents, fatalities,
       ROUND(100 * fatalities / accidents, 1)  AS fatalities_per_100_accidents,
       ROUND(100 * fatalities / casualties, 1) AS fatalities_per_100_casualties
FROM (
    SELECT Location, City,
           MIN(Road_Type)                AS Road_Type_Main,
           COUNT(*)                      AS accidents,
           SUM(Number_of_Casualties)     AS casualties,
           SUM(Number_of_Fatalities)     AS fatalities
    FROM accidents
    GROUP BY Location, City
) AS loc
WHERE accidents >= 100
ORDER BY fatalities_per_100_accidents DESC
LIMIT 10;


/* -------------------------------------------------------------------------------------
   Q20. DRIVER AGE GROUP ANALYSIS
   QUESTION : Do certain age groups have worse outcomes?
   WHAT IT DOES: Accidents, severe %, fatal % and male share per age group.
   LOOK FOR : Whether differences are BIG or small. Small differences mean age is not a strong
              driver - saying so honestly is a good interview answer.
   ------------------------------------------------------------------------------------- */
SELECT Age_Group,
       COUNT(*)                                                       AS accidents,
       ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)               AS pct_of_accidents,
       ROUND(100 * SUM(Accident_Severity <> 'Minor') / COUNT(*), 1)   AS severe_pct,
       ROUND(100 * SUM(Accident_Severity = 'Fatal')  / COUNT(*), 1)   AS fatal_pct,
       ROUND(100 * SUM(Driver_Gender = 'Male') / COUNT(*), 1)         AS male_pct
FROM accidents
GROUP BY Age_Group
ORDER BY Age_Group;


/* -------------------------------------------------------------------------------------
   Q21. SPEED LIMIT vs SEVERITY
   QUESTION : How does severity change as the speed limit rises?
   WHAT IT DOES: Severity split per speed limit; CASE converts the three severities to %.
   LOOK FOR : Fatal % climbing with the speed limit. CAUTION: high limits sit on highways and
              expressways, so this also reflects the road environment.
   ------------------------------------------------------------------------------------- */
SELECT Speed_Limit,
       COUNT(*)                                                       AS accidents,
       ROUND(100 * SUM(Accident_Severity = 'Minor')   / COUNT(*), 1)  AS minor_pct,
       ROUND(100 * SUM(Accident_Severity = 'Serious') / COUNT(*), 1)  AS serious_pct,
       ROUND(100 * SUM(Accident_Severity = 'Fatal')   / COUNT(*), 1)  AS fatal_pct,
       ROUND(AVG(Number_of_Casualties), 2)                            AS avg_casualties
FROM accidents
GROUP BY Speed_Limit
ORDER BY Speed_Limit;


/* -------------------------------------------------------------------------------------
   Q22. LIGHT CONDITION vs SEVERITY
   QUESTION : Is darkness - and especially unlit roads - more dangerous?
   WHAT IT DOES: Severity split per light condition.
   LOOK FOR : The jump in Fatal % from 'Darkness - Lights Lit' to 'Darkness - No Lights'.
   ------------------------------------------------------------------------------------- */
SELECT Light_Condition,
       COUNT(*)                                                       AS accidents,
       ROUND(100 * SUM(Accident_Severity <> 'Minor') / COUNT(*), 1)   AS severe_pct,
       ROUND(100 * SUM(Accident_Severity = 'Fatal')  / COUNT(*), 1)   AS fatal_pct
FROM accidents
GROUP BY Light_Condition
ORDER BY fatal_pct DESC;


/* -------------------------------------------------------------------------------------
   Q23. HIGH-RISK ACCIDENT IDENTIFICATION
   QUESTION : How many accidents fall in each risk category, and what do the worst ones look like?
   WHAT IT DOES: Part (a) counts the Risk_Category rule created in Python (Critical = Fatal with
                 2+ deaths or alcohol). Part (b) lists the 15 worst Critical accidents.
   LOOK FOR : Common characteristics (night, highway, alcohol, bus/truck) among Critical accidents.
   ------------------------------------------------------------------------------------- */
-- (a) distribution
SELECT Risk_Category,
       COUNT(*)                                          AS accidents,
       ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)  AS pct_of_total,
       SUM(Number_of_Fatalities)                         AS fatalities
FROM accidents
GROUP BY Risk_Category
ORDER BY FIELD(Risk_Category, 'Critical', 'High', 'Medium', 'Low');

-- (b) the 15 worst critical accidents
SELECT Accident_ID, Accident_Date, Accident_Time, City, Location, Vehicle_Type, Weather_Condition,
       Light_Condition, Alcohol_Involved, Number_of_Casualties, Number_of_Fatalities
FROM accidents
WHERE Risk_Category = 'Critical'
ORDER BY Number_of_Fatalities DESC, Number_of_Casualties DESC
LIMIT 15;


/* -------------------------------------------------------------------------------------
   Q24. RANK LOCATIONS INSIDE EACH CITY   (CTE + RANK() with PARTITION BY)
   QUESTION : What is the most dangerous location in EACH city?
   WHAT IT DOES: The CTE aggregates per location; RANK() OVER (PARTITION BY City ...) restarts the
                 ranking for every city; the outer query keeps the top 2 per city.
   LOOK FOR : Each city's #1 hotspot, which may be different from the national top 10.
   ------------------------------------------------------------------------------------- */
WITH loc_stats AS (
    SELECT City, Location,
           COUNT(*)                  AS accidents,
           SUM(Number_of_Fatalities) AS fatalities
    FROM accidents
    GROUP BY City, Location
),
ranked AS (
    SELECT City, Location, accidents, fatalities,
           RANK() OVER (PARTITION BY City ORDER BY fatalities DESC, accidents DESC) AS city_rank
    FROM loc_stats
)
SELECT City, city_rank, Location, accidents, fatalities
FROM ranked
WHERE city_rank <= 2
ORDER BY City, city_rank;


/* -------------------------------------------------------------------------------------
   Q25. CITIES WORSE THAN THE NATIONAL AVERAGE   (CTE + CROSS JOIN)
   QUESTION : Which cities have a higher share of severe accidents than the overall average?
   WHAT IT DOES: One CTE calculates the overall severe %, another calculates each city's severe %;
                 CROSS JOIN attaches the single overall value to every city row.
   LOOK FOR : Cities with a positive 'gap' - they need above-average safety investment.
   ------------------------------------------------------------------------------------- */
WITH overall AS (
    SELECT 100 * SUM(Accident_Severity <> 'Minor') / COUNT(*) AS overall_severe_pct
    FROM accidents
),
city_stats AS (
    SELECT City,
           COUNT(*)                                                   AS accidents,
           SUM(Number_of_Fatalities)                                  AS fatalities,
           100 * SUM(Accident_Severity <> 'Minor') / COUNT(*)         AS city_severe_pct
    FROM accidents
    GROUP BY City
)
SELECT c.City, c.accidents, c.fatalities,
       ROUND(c.city_severe_pct, 1)                      AS city_severe_pct,
       ROUND(o.overall_severe_pct, 1)                   AS overall_severe_pct,
       ROUND(c.city_severe_pct - o.overall_severe_pct, 1) AS gap_points
FROM city_stats c
CROSS JOIN overall o
ORDER BY gap_points DESC;


/* -------------------------------------------------------------------------------------
   Q26. LOCATION'S SHARE OF ITS CITY'S ACCIDENTS   (JOIN of two aggregated CTEs)
   QUESTION : Is a city's problem concentrated in one or two spots?
   WHAT IT DOES: Joins the location totals to the city totals on City and calculates the share.
   LOOK FOR : Locations with a large share (>25%) - fixing one junction would help the whole city.
   ------------------------------------------------------------------------------------- */
WITH loc AS (
    SELECT City, Location, COUNT(*) AS loc_accidents
    FROM accidents GROUP BY City, Location
),
city AS (
    SELECT City, COUNT(*) AS city_accidents
    FROM accidents GROUP BY City
)
SELECT l.City, l.Location, l.loc_accidents, c.city_accidents,
       ROUND(100 * l.loc_accidents / c.city_accidents, 1) AS pct_of_city
FROM loc l
JOIN city c ON c.City = l.City
ORDER BY pct_of_city DESC
LIMIT 10;


/* -------------------------------------------------------------------------------------
   Q27. LOCATION x TIME-PERIOD HOTSPOTS
   QUESTION : Where AND when should enforcement be deployed?
   WHAT IT DOES: Groups by location and time period, keeps combinations with at least 25 accidents
                 (HAVING) and sorts by fatal %.
   LOOK FOR : A highway at late night with a very high fatal % -> a specific patrol shift.
   ------------------------------------------------------------------------------------- */
SELECT Location, City, Time_Period,
       COUNT(*)                                                    AS accidents,
       SUM(Number_of_Fatalities)                                   AS fatalities,
       ROUND(100 * SUM(Accident_Severity = 'Fatal') / COUNT(*), 1) AS fatal_pct
FROM accidents
GROUP BY Location, City, Time_Period
HAVING COUNT(*) >= 25
ORDER BY fatal_pct DESC
LIMIT 10;


/* -------------------------------------------------------------------------------------
   Q28. MONTHLY TREND WITH 3-MONTH MOVING AVERAGE   (window frame)
   QUESTION : What is the underlying trend once month-to-month noise is smoothed out?
   WHAT IT DOES: Counts accidents per year+month, then AVG() OVER (ROWS BETWEEN 2 PRECEDING AND
                 CURRENT ROW) averages the current and previous 2 months.
   LOOK FOR : The smoothed line makes the 2020 dip and the recovery easy to see.
   ------------------------------------------------------------------------------------- */
WITH monthly AS (
    SELECT Year, Month_Num, COUNT(*) AS accidents
    FROM accidents
    GROUP BY Year, Month_Num
)
SELECT Year, Month_Num, accidents,
       ROUND(AVG(accidents) OVER (ORDER BY Year, Month_Num
                                  ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1) AS moving_avg_3m
FROM monthly
ORDER BY Year, Month_Num;


/* -------------------------------------------------------------------------------------
   Q29. DANGEROUS CONDITION COMBINATIONS (weather x light x alcohol using CASE)
   QUESTION : Which combinations of conditions are the deadliest?
   WHAT IT DOES: CASE builds a simple "risk factor count" per accident (fog/heavy rain, darkness without
                 lights, alcohol, speed limit >= 80). We then see how severity grows with the count.
   LOOK FOR : Fatal % rising step by step with the number of risk factors (3 means '3 or more') - the strongest
              evidence that risks compound.
   ------------------------------------------------------------------------------------- */
SELECT risk_factors,
       COUNT(*)                                                    AS accidents,
       ROUND(100 * SUM(Accident_Severity <> 'Minor') / COUNT(*), 1) AS severe_pct,
       ROUND(100 * SUM(Accident_Severity = 'Fatal')  / COUNT(*), 1) AS fatal_pct
FROM (
    SELECT Accident_Severity,
           LEAST(3,                                   -- cap at 3 so the "3+" bucket is large enough to trust
                 (CASE WHEN Weather_Condition IN ('Fog', 'Heavy Rain')  THEN 1 ELSE 0 END)
               + (CASE WHEN Light_Condition = 'Darkness - No Lights'    THEN 1 ELSE 0 END)
               + (CASE WHEN Alcohol_Involved = 'Yes'                    THEN 1 ELSE 0 END)
               + (CASE WHEN Speed_Limit >= 80                           THEN 1 ELSE 0 END)) AS risk_factors
    FROM accidents
) AS t
GROUP BY risk_factors
ORDER BY risk_factors;
