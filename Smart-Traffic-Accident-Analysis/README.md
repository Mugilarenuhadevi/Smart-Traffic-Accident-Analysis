
# Smart Traffic Accident Analysis

## Project Overview

This is a data analytics project that explores traffic accident patterns using Python, Pandas, SQL, and data visualizations.

The project focuses on understanding how accident frequency and severity vary across different times, weather conditions, road conditions, vehicle types, and locations. The analysis helps identify patterns in the dataset and suggest areas for further road safety investigation.

**Note:** This project uses synthetic sample data. The findings represent the generated dataset and should not be interpreted as real-world accident statistics.

## Objectives

- Clean and prepare traffic accident data for analysis.
- Explore accident patterns by time, location, weather, and road conditions.
- Compare accident severity across different vehicle types and other factors.
- Use SQL queries to examine the data.
- Create visualizations to communicate important patterns.
- Summarize findings and suggest possible road safety improvements.

## Tools and Technologies

- **Python** – Data processing and analysis
- **Pandas and NumPy** – Data cleaning and manipulation
- **Matplotlib and Seaborn** – Data visualization
- **SQL / MySQL** – Database queries and analysis
- **Jupyter Notebook** – Interactive analysis
- **CSV** – Dataset storage and exchange

Power BI documentation and a theme file are also included as resources for developing an interactive dashboard. A completed Power BI dashboard file is not included in this repository.

## Dataset

The project includes a raw dataset and a cleaned dataset.

- `data/raw/raw_accidents.csv` – Raw sample accident data
- `data/cleaned/cleaned_accidents.csv` – Cleaned dataset
- `data/cleaned/cleaning_report.txt` – Data cleaning report

The data is generated using the project's Python script. It includes sample accident records and deliberately introduced data-quality issues for practicing data cleaning.

**Important:** The dataset is synthetic and does not represent verified accident records from India or any other country.

## Project Workflow

1. Generate the sample dataset.
2. Inspect and clean missing, duplicate, and inconsistent values.
3. Explore accident patterns using Python.
4. Create charts to compare accident frequency and severity.
5. Write SQL queries to investigate the dataset.
6. Summarize the findings and possible safety recommendations.

## Exploratory Data Analysis

The repository contains visualizations covering topics such as:

- Accidents by year, month, day, and hour
- Accidents by weather and road conditions
- Accident severity distribution
- Accidents by vehicle type and location
- Fatalities and casualties over time
- Alcohol involvement
- Speed limits and accident severity
- Age groups and lighting conditions
- Accident patterns by day and hour

The charts are available in the `visualizations/` folder.

## SQL Analysis

The file `sql/accident_analysis.sql` contains SQL scripts for examining traffic accident data.

The queries are intended to explore patterns, compare categories, summarize accident counts, and investigate factors associated with accident severity.

To reproduce the analysis, review the SQL script and configure the database and file paths for your local environment.

## Key Areas of Analysis

The project investigates questions such as:

- At what times are accidents most frequent in the sample dataset?
- How does accident severity vary across weather conditions?
- Which vehicle categories have higher proportions of severe outcomes?
- How do road and lighting conditions relate to accident severity?
- Which locations have higher accident counts in the generated data?
- What patterns appear in records involving alcohol?

The detailed findings are documented in `docs/key_insights.md`. Since the dataset is synthetic, these findings are exploratory rather than evidence of real-world causal relationships.

## Repository Structure

```text
Smart-Traffic-Accident-Analysis/
├── data/
│   ├── raw/
│   └── cleaned/
├── docs/
│   ├── interview_preparation.md
│   └── key_insights.md
├── notebooks/
│   └── accident_analysis.ipynb
├── powerbi/
│   ├── accident_theme.json
│   └── dashboard_documentation.md
├── python/
│   ├── generate_dataset.py
│   ├── data_cleaning.py
│   ├── exploratory_analysis.py
│   └── load_to_mysql.py
├── sql/
│   └── accident_analysis.sql
├── visualizations/
├── requirements.txt
└── README.md
```

## Getting Started

### Requirements

- Python installed on your computer
- The packages listed in `requirements.txt`
- MySQL, if you want to run the database analysis





## Possible Future Improvements

- Analyze a verified public traffic accident dataset.
- Develop and include a completed Power BI dashboard.
- Add interactive location-based visualizations.
- Apply statistical methods to investigate relationships between accident factors and severity.
- Compare results across regions and time periods using real data.

## Author

**Mugila Renuha devi**

GitHub: [Mugilarenuhadevi](https://github.com/Mugilarenuhadevi)
