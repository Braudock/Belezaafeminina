"""
worldbank_population_dashboard.py
---------------------------------

This script retrieves population and land area data for each country from the
World Bank's public API and produces a CSV file and interactive dashboard.

Steps performed by this script:

1. Query the World Bank API for the list of all countries, excluding
   aggregated regions.
2. Fetch the total population for each country for a specific year (default
   2023). If data is missing for that year, it is omitted from the output.
3. Fetch the land area (in square kilometers) for each country for a
   specific year (default 2021) because land area data is often lagged.
4. Merge the population and land area data into a single pandas DataFrame.
5. Save the data to a CSV file.
6. Generate interactive Plotly charts:
   - A bar chart of the top 15 countries by population.
   - A bar chart of the top 15 countries by population density.
   - A scatter plot of population versus land area (log scales) for the
     largest 50 countries.
7. Combine these charts into a simple HTML dashboard.

Usage:
    python worldbank_population_dashboard.py

Requirements:
    This script uses the `requests`, `pandas`, and `plotly` libraries, all of
    which are available in the provided environment. It does not rely on
    external network access beyond the World Bank API endpoints.
"""

import pandas as pd
import plotly.express as px
import plotly.io as pio
import requests

WORLD_BANK_COUNTRY_URL = "https://api.worldbank.org/v2/country?format=json&per_page=4000"
WORLD_BANK_POPULATION_URL = (
    "https://api.worldbank.org/v2/country/all/indicator/SP.POP.TOTL?date={year}&format=json&per_page=4000"
)
WORLD_BANK_LAND_AREA_URL = (
    "https://api.worldbank.org/v2/country/all/indicator/AG.LND.TOTL.K2?date={year}&format=json&per_page=4000"
)

def fetch_countries():
    resp = requests.get(WORLD_BANK_COUNTRY_URL)
    resp.raise_for_status()
    data = resp.json()[1]
    return [c["id"] for c in data if c["region"]["value"] != "Aggregates"]

def fetch_indicator_data(url_template, year):
    url = url_template.format(year=year)
    resp = requests.get(url)
    resp.raise_for_status()
    observations = resp.json()[1]
    data_by_country = {}
    for obs in observations:
        iso3 = obs["countryiso3code"]
        value = obs["value"]
        if value is not None:
            data_by_country[iso3] = value
    return data_by_country

def build_dataset(pop_year=2023, area_year=2021):
    countries = fetch_countries()
    pop_data = fetch_indicator_data(WORLD_BANK_POPULATION_URL, pop_year)
    area_data = fetch_indicator_data(WORLD_BANK_LAND_AREA_URL, area_year)
    rows = []
    for iso3 in countries:
        population = pop_data.get(iso3)
        area = area_data.get(iso3)
        if population is not None and area is not None and area > 0:
            rows.append({"Country Code": iso3, "Population": population, "Land Area": area})
    df = pd.DataFrame(rows)
    return df.sort_values(by="Population", ascending=False).reset_index(drop=True)

def fetch_country_names():
    resp = requests.get(WORLD_BANK_COUNTRY_URL)
    resp.raise_for_status()
    data = resp.json()[1]
    return {c["id"]: c["name"] for c in data}

def augment_country_names(df):
    name_map = fetch_country_names()
    df["Country"] = df["Country Code"].map(name_map)
    return df

def create_charts(df):
    top_pop = df.head(15)
    fig1 = px.bar(
        top_pop,
        x="Country",
        y="Population",
        title="Top 15 Countries by Population (2023)",
        labels={"Population": "Population", "Country": "Country"},
    )
    fig1.update_layout(xaxis_tickangle=-45)

    df["Density"] = df["Population"] / df["Land Area"]
    top_density = df.sort_values("Density", ascending=False).head(15)
    fig2 = px.bar(
        top_density,
        x="Country",
        y="Density",
        title="Top 15 Countries by Population Density (2023)",
        labels={"Density": "People per km²", "Country": "Country"},
    )
    fig2.update_layout(xaxis_tickangle=-45)

    top50 = df.head(50)
    fig3 = px.scatter(
        top50,
        x="Land Area",
        y="Population",
        size="Density",
        color="Population",
        hover_name="Country",
        title="Population vs Land Area (Top 50 Countries)",
        labels={"Land Area": "Land Area (km²)", "Population": "Population", "Density": "Density"},
    )
    fig3.update_layout(
        xaxis_type="log",
        yaxis_type="log",
        legend_title="Population",
    )

    return [fig1, fig2, fig3]

def save_dashboard(charts, output_html):
    html_parts = [
        "<!DOCTYPE html>",
        "<html lang=\"en\">",
        "<head>",
        "    <meta charset=\"UTF-8\">",
        "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">",
        "    <title>World Population Dashboard</title>",
        "    <style>",
        "        body { font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f9f9f9; }",
        "        .container { width: 95%; max-width: 1200px; margin: auto; padding: 20px; }",
        "        h1 { text-align: center; color: #333; margin-bottom: 20px; }",
        "        .chart { margin-bottom: 40px; background-color: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }",
        "    </style>",
        "</head>",
        "<body>",
        "    <div class=\"container\">",
        "        <h1>World Population Dashboard (2023)</h1>",
    ]
    for i, fig in enumerate(charts, 1):
        chart_div = pio.to_html(fig, include_plotlyjs='cdn', full_html=False)
        html_parts.append(f"        <div class=\"chart\" id=\"chart{i}\">{chart_div}</div>")
    html_parts.extend([
        "    </div>",
        "</body>",
        "</html>",
    ])
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html_parts))

def main():
    print("Fetching and assembling data...")
    df = build_dataset(pop_year=2023, area_year=2021)
    df = augment_country_names(df)
    csv_file = 'world_population_2023.csv'
    df.to_csv(csv_file, index=False)
    print(f"Saved population data to {csv_file}.")
    charts = create_charts(df)
    html_file = 'world_population_dashboard.html'
    save_dashboard(charts, html_file)
    print(f"Dashboard saved to {html_file}.")
    print("Done.")

if __name__ == '__main__':
    main()
