# Hyderabad EV Charging Analytics

An end-to-end portfolio project combining a **clearly labeled synthetic EV
charging activity dataset** with a separate, small snapshot of real public
OpenStreetMap charging-site references. The analytics features demonstrate
Python, SQL, Excel, Power BI, dashboards, and a time-series modeling workflow
without presenting generated sessions as real company records.

**Live dashboard:** [hyderabad-ev-charging-analytics.netlify.app](https://hyderabad-ev-charging-analytics.netlify.app/)

## What is real and what is synthetic

- **Synthetic:** 30 example stations, 90 chargers, 500 example customers, 15,000
  charging sessions, and 500 maintenance events. All synthetic activity KPIs,
  trends, revenues, rankings, and forecasting inputs are for practice only.
- **Public mapped references:** three OpenStreetMap objects tagged as charging
  stations in the query area in the captured snapshot. These are not a complete
  station inventory and do not establish current operation.
- **Not available in the public reference:** real session histories, usage,
  delivered energy, prices, revenue, outages, wait times, or utilization. No
  business conclusion from the synthetic data should be described as a real
  Hyderabad market finding.

## Business questions demonstrated

- Which synthetic locations and stations handle the most completed sessions?
- When are synthetic charging sessions busiest?
- How do generated energy and estimated revenue vary by location and month?
- How can a station-hour demand forecast be evaluated using a chronological
  train/test split?
- How can real mapped site references and source-data limitations be reported
  separately and transparently?

## Project layout

```text
data/
  raw/                 Reproducible synthetic CSVs (generated)
  reference/           Real, separately sourced OpenStreetMap snapshot
  processed/           Cleaned sessions and hourly demand (generated)
notebooks/
  01_data_cleaning_eda.ipynb              Synthetic data cleaning and EDA
  01_real_charging_site_audit.ipynb        Public map-data coverage audit
scripts/
  generate_data.py                        Reproducible synthetic-data generator
  fetch_real_data.py                      Optional Overpass snapshot refresh
  build_dashboard.py                      Browser dashboard builder
  build_excel_report.py                   Excel audit workbook builder
sql/
  charging_site_analysis.sql              Queries for the real OSM reference
power_bi/
  README.md                               Real-site Power BI instructions
reports/
  dashboard.html                          Generated browser dashboard
  hyderabad_charging_sites.xlsx            Generated Excel inventory report
  figures/                                 EDA and site-reference charts
site/
  index.html                               Netlify-ready static site bundle
```

## Run the project

Use Python 3.11–3.13 and install dependencies into the interpreter used for
Jupyter:

```powershell
python -m pip install -r requirements.txt
python scripts\generate_data.py
```

Open `notebooks/01_data_cleaning_eda.ipynb`, choose the compatible Python
interpreter, and run all cells. This writes `data/processed/cleaned_sessions.csv`,
`data/processed/hourly_station_demand.csv`, and three synthetic EDA charts.

Build the browser dashboard and Excel reference workbook:

```powershell
python scripts\build_dashboard.py
python scripts\build_excel_report.py
```

Open `reports/dashboard.html` in a browser. The dashboard presents synthetic
activity KPIs and real map references in separate, labeled sections.

The dashboard build also prepares `site/` as a static Netlify publish directory.
After signing in to Netlify CLI, deploy it with:

```powershell
npx netlify-cli@17.38.1 deploy --prod --dir site
```

The first deployment will prompt you to create or link a Netlify site and then
prints its public URL. A deploy link cannot be created until Netlify
authentication and site ownership are authorized.

The optional refresh uses the public Overpass API and may be rate-limited or
unavailable. The last checked-in CSV works offline:

```powershell
python scripts\fetch_real_data.py
```

## Synthetic data model

| File | Grain | Primary key |
|---|---|---|
| `stations.csv` | One example station | `station_id` |
| `chargers.csv` | One example charger | `charger_id` |
| `customers.csv` | One example customer | `customer_id` |
| `charging_sessions.csv` | One generated session | `session_id` |
| `maintenance.csv` | One generated maintenance event | `maintenance_id` |

The generator is deterministic with a fixed seed. Revenue is a generated
estimate calculated as generated energy multiplied by a generated tariff. The
data is deliberately synthetic—not scraped or supplied by a charging operator.

## Real reference source

`data/reference/charging_sites_openstreetmap.csv` records the source OSM object,
coordinates, available tags, source timestamp, and direct object URL for the
snapshot query. Objects with no mapped name remain unnamed. OSM's coverage may
be incomplete, and mapped existence does not verify that a charger is currently
available.

Map data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright)
and is available under the [Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/).

## Portfolio / resume wording

Describe this honestly as a **synthetic-data EV charging analytics portfolio
project**. You can state that you generated 15,000 practice sessions, cleaned
and analyzed the activity, built a dashboard, and created an hourly demand
forecasting workflow—after you run and evaluate that model. Do not claim the
synthetic metrics are results from a real Hyderabad operator.
