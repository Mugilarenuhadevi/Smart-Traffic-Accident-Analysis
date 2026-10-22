# Key Insights & Recommendations

> Every number below is calculated from `data/cleaned/cleaned_accidents.csv` by `python/exploratory_analysis.py`.

**Definitions:** *Severe* = Serious or Fatal accident. *Fatal %* = share of accidents classified Fatal. *Fatality rate* = fatalities per 100 casualties.

## 0. Overview

- **12,000** accidents, **19,839** casualties, **1,634** fatalities (8.2 deaths per 100 casualties; 1.65 casualties per accident).
- Period: 2019-01-01 to 2023-12-31. Busiest year: **2023** (2,756); quietest: **2020** (1,810).
- Severity mix: Minor 61.9%, Serious 28.9%, Fatal 9.2%.

## 1. When do accidents happen?

- **DATA FINDING:** Peak hours are 18:00 (965), 19:00 (925), 17:00 (760). Busiest day: **Saturday** (1,930); quietest: Tuesday (1,574). Busiest month: **October** (1,144).
- **DATA FINDING:** Late-night accidents (12-4 AM) are fewer (742 vs 4,045 in the 4-8 PM peak) but deadlier: 15.6% fatal vs 6.9% at midday.
- **RECOMMENDATION:** Concentrate traffic police and ambulance coverage between 17:00 and 20:00 (highest volume); add separate drunk-driving and speed checks at night, because fewer accidents there still end more often in death.

## 2. Weather

- **DATA FINDING:** Share of severe accidents by weather: Fog 52.4% (fatal 13.4%); Heavy Rain 50.2% (fatal 15.7%); Light Rain 41.9% (fatal 10.6%); Cloudy 37.1% (fatal 8.6%); Clear 35.1% (fatal 7.9%).
- **DATA FINDING:** **Fog** is the most severe condition: 52.4% severe vs 35.1% in clear weather.
- **RECOMMENDATION:** Trigger weather-based alerts (SMS / variable-message signs) for fog and heavy rain, with temporary speed reductions and fog lights on the affected corridors.

## 3. Road condition

- **DATA FINDING:** Severe-accident share by road condition: Wet 45.2%; Damaged (Potholes) 44.2%; Under Construction 39.8%; Dry 35.0%.
- **DATA FINDING:** Compared with dry roads (35.0% severe), wet roads are +10.2 points and damaged roads +9.2 points.
- **RECOMMENDATION:** Resurface pothole-damaged stretches, improve drainage and anti-skid surfacing where roads are often wet, and add warning signs / barriers around construction zones.

## 4. Vehicle types

- **DATA FINDING:** Most frequent: **Two-Wheeler** (4,111 accidents, 34.3%), then Car (25.0%) and Truck (15.3%).
- **DATA FINDING:** Highest fatal share: **Truck** (14.6%), then Bus (12.6%).
- **RECOMMENDATION:** Run helmet / rider-safety campaigns and enforcement aimed at two-wheeler users; add speed limiters and driver-fatigue rules for truck operators.

## 5. Locations

- **DATA FINDING:** Most accidents: NH44 Singhu Border (420), Mathura Road Badarpur (374), Western Express Highway (369).
- **DATA FINDING:** Highest fatal share: Mumbai-Pune Expressway Khandala - Pune (33.8% fatal), Yamuna Expressway Entry - Delhi (28.9% fatal), Nehru Outer Ring Exit 12 - Hyderabad (28.3% fatal).
- **DATA FINDING:** City with most accidents: **Delhi** (1,818); most fatalities: **Delhi** (312).
- **RECOMMENDATION:** Install speed cameras, better lighting and emergency response points at Mumbai-Pune Expressway Khandala and Yamuna Expressway Entry first, because the same number of accidents there costs more lives.

## 6. Alcohol

- **DATA FINDING:** Alcohol was involved in **6.5%** of accidents with a known alcohol status.
- **DATA FINDING:** 29.7% of alcohol-related accidents were fatal vs 7.6% of the others (**3.9x** higher).
- **DATA FINDING:** Alcohol share is 17.2% between 9 PM-4 AM vs 4.3% during the rest of the day.
- **RECOMMENDATION:** Run breathalyser checkpoints at night and on weekends at the highest-risk locations, and fund a public awareness campaign on drink-driving.

## 7. Weekend vs weekday

- **DATA FINDING:** Weekend days average 7.0 accidents per day vs 6.4 on weekdays. Fatal share: weekend 9.9% vs weekday 8.8%. Alcohol share: weekend 8.8% vs weekday 5.5%.
- **RECOMMENDATION:** Schedule extra patrols and trauma-centre staffing on the busiest days (Saturday and Friday) and on weekend nights, rather than spreading resources evenly across the week.

## 8. Speed, lighting and driver age

- **DATA FINDING (speed):** Fatal share by speed limit: 30 km/h 0.3%, 40 km/h 1.0%, 50 km/h 2.0%, 60 km/h 8.3%, 70 km/h 10.9%, 80 km/h 15.2%, 100 km/h 24.7%, 120 km/h 41.1%. Caution: speed limit is linked to road type (high limits are on expressways/highways), so this shows the *environment's* risk, not only driver speed.
- **DATA FINDING (lighting):** Fatal share by light condition: Darkness - Lights Lit 11.7%, Darkness - No Lights 22.0%, Dawn/Dusk 8.5%, Daylight 7.1%.
- **DATA FINDING (age):** Fatal share by driver age group: 18-24 8.4%, 25-34 8.5%, 35-49 10.1%, 50-64 8.9%, 65+ 9.9%.
- **RECOMMENDATION (speed):** Enforce limits with average-speed cameras on the highest-limit corridors; add rumble strips and median barriers on expressways.
- **RECOMMENDATION (lighting):** Fix street lighting on unlit stretches - **Darkness - No Lights** has the highest fatal share (22.0%).
- **DATA FINDING (age):** Fatal share differs by only 1.7 points between age groups, so age alone is NOT a strong risk factor here; road and environment factors matter more.

## 9. Risk categories

- **DATA FINDING:** Low 61.9%, Medium 17.9%, High 15.9%, Critical 4.3% of accidents (rule-based `Risk_Category`; see data_cleaning.py).
- **DATA FINDING:** 13 mass-casualty accidents (10+ casualties) = 0.11% of accidents but 6.9% of all fatalities; Trucks are the most common vehicle in these events.
- **RECOMMENDATION:** Pre-plan multi-ambulance dispatch rules for heavy-vehicle crashes on highways (they generate the mass-casualty events).
