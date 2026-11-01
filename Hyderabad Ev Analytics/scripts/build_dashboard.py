"""Build a standalone dashboard for synthetic analytics and real OSM references."""

from __future__ import annotations

from html import escape
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
DATA_DIR = ROOT / "data" / "processed"
REFERENCE_PATH = ROOT / "data" / "reference" / "charging_sites_openstreetmap.csv"
OUTPUT = ROOT / "reports" / "dashboard.html"
DEPLOY_DIR = ROOT / "site"


def format_number(value: float, decimals: int = 0) -> str:
    return f"{value:,.{decimals}f}"


def main() -> None:
    sessions = pd.read_csv(DATA_DIR / "cleaned_sessions.csv")
    stations = pd.read_csv(RAW_DIR / "stations.csv")
    completed = sessions.loc[sessions["session_status"].eq("Completed")].copy()

    completed_count = len(completed)
    completion_rate = completed_count / len(sessions) * 100
    active_stations = completed["station_id"].nunique()
    energy_total = completed["energy_kwh"].sum()
    revenue_total = completed["revenue_inr"].sum()
    average_duration = completed["duration_minutes"].mean()

    location_summary = (
        completed.merge(
            stations[["station_id", "location"]],
            on="station_id",
            validate="many_to_one",
        )
        .groupby("location", as_index=False)
        .agg(
            sessions=("session_id", "nunique"),
            energy_kwh=("energy_kwh", "sum"),
            revenue_inr=("revenue_inr", "sum"),
        )
        .sort_values("sessions", ascending=False)
        .head(8)
    )
    location_rows = "\n".join(
        "<tr>"
        f"<td>{escape(row.location)}</td>"
        f"<td>{format_number(row.sessions)}</td>"
        f"<td>{format_number(row.energy_kwh, 1)}</td>"
        f"<td>₹{format_number(row.revenue_inr, 0)}</td>"
        "</tr>"
        for row in location_summary.itertuples(index=False)
    )

    monthly_summary = (
        completed.assign(
            month=pd.to_datetime(completed["session_start"]).dt.to_period("M").astype(str)
        )
        .groupby("month", as_index=False)
        .agg(
            sessions=("session_id", "nunique"),
            revenue_inr=("revenue_inr", "sum"),
        )
        .sort_values("month")
    )
    month_rows = "\n".join(
        "<tr>"
        f"<td>{escape(row.month)}</td>"
        f"<td>{format_number(row.sessions)}</td>"
        f"<td>₹{format_number(row.revenue_inr, 0)}</td>"
        "</tr>"
        for row in monthly_summary.itertuples(index=False)
    )

    reference_rows = ""
    reference_count = 0
    if REFERENCE_PATH.exists():
        references = pd.read_csv(REFERENCE_PATH)
        reference_count = len(references)
        reference_rows = "\n".join(
            "<tr>"
            f"<td>{escape(str(row.brand) if pd.notna(row.brand) and str(row.brand).strip() else 'Name not mapped')}</td>"
            f"<td>{escape(row.osm_type.title())} #{int(row.osm_id)}</td>"
            f"<td>{row.latitude:.6f}, {row.longitude:.6f}</td>"
            f"<td><a href=\"{escape(row.source_url if pd.notna(row.source_url) and str(row.source_url).strip() else f'https://www.openstreetmap.org/{row.osm_type}/{int(row.osm_id)}')}\" target=\"_blank\" rel=\"noreferrer\">OSM record</a></td>"
            "</tr>"
            for row in references.itertuples(index=False)
        )

    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="EV charging portfolio analytics dashboard with synthetic activity and separate real map references">
  <title>Hyderabad EV Charging | Analytics dashboard</title>
  <style>
    :root {{ color-scheme:light; --ink:#172a35; --muted:#647782; --teal:#087e78; --teal-light:#e4f4f1; --line:#e4ecea; --paper:#fff; --bg:#f3f7f6; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--ink); font:15px/1.5 "Segoe UI",Arial,sans-serif; }}
    .wrap {{ max-width:1180px; margin:0 auto; padding:34px 24px 48px; }}
    .hero {{ position:relative; overflow:hidden; padding:34px; border-radius:22px; color:#fff; background:linear-gradient(120deg,#123f48,#087e78 70%,#21a58e); }}
    .eyebrow {{ margin:0 0 8px; color:#bbebe0; font-size:12px; font-weight:700; letter-spacing:.14em; text-transform:uppercase; }}
    h1 {{ max-width:720px; margin:0; font-size:clamp(29px,4vw,43px); line-height:1.12; }}
    .hero p:last-child {{ max-width:700px; margin:14px 0 0; color:#e1f3ef; }}
    .badge {{ display:inline-flex; margin-top:20px; padding:6px 11px; border:1px solid #ffffff55; border-radius:99px; font-size:12px; }}
    .section-title {{ margin:30px 0 14px; font-size:19px; }}
    .kpis {{ display:grid; grid-template-columns:repeat(3,1fr); gap:14px; }}
    .card {{ min-width:0; padding:20px; border:1px solid var(--line); border-radius:15px; background:var(--paper); box-shadow:0 4px 18px #1c45460a; }}
    .kpi-label {{ color:var(--muted); font-size:13px; }}
    .kpi-value {{ margin-top:5px; font-size:clamp(23px,3vw,30px); font-weight:700; letter-spacing:-.03em; }}
    .kpi-note {{ margin-top:2px; color:var(--muted); font-size:12px; }}
    .charts {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:16px; }}
    .chart-card {{ padding:18px; }}
    .chart-card h3 {{ margin:0 0 10px; font-size:15px; }}
    .chart-card img {{ display:block; width:100%; height:auto; }}
    .chart-wide {{ grid-column:1/-1; }}
    .chart-wide img {{ max-width:800px; margin:0 auto; }}
    .tables {{ display:grid; grid-template-columns:1.2fr .8fr; gap:16px; }}
    .table-card {{ padding:0; overflow:hidden; }}
    .table-card h3 {{ margin:0; padding:18px 18px 10px; font-size:15px; }}
    .table-scroll {{ overflow-x:auto; }}
    table {{ width:100%; border-collapse:collapse; font-size:13px; }}
    th,td {{ padding:10px 14px; border-bottom:1px solid var(--line); text-align:left; white-space:nowrap; }}
    th {{ color:var(--muted); background:#f8fbfa; font-size:11px; letter-spacing:.04em; text-transform:uppercase; }}
    tr:last-child td {{ border-bottom:0; }}
    .note {{ margin-top:20px; padding:15px 18px; border-left:3px solid var(--teal); border-radius:8px; background:var(--teal-light); color:#34545a; font-size:13px; }}
    a {{ color:var(--teal); font-weight:600; }}
    footer {{ margin-top:24px; color:var(--muted); font-size:12px; }}
    .project-credit {{ margin:8px 0 0; color:var(--ink); font-size:14px; font-weight:600; text-align:center; }}
    @media(max-width:760px) {{ .wrap{{padding:18px 14px 32px}} .hero{{padding:26px 22px}} .kpis{{grid-template-columns:repeat(2,1fr)}} .charts,.tables{{grid-template-columns:1fr}} .chart-wide{{grid-column:auto}} }}
    @media(max-width:430px) {{ .kpis{{grid-template-columns:1fr}} }}
  </style>
</head>
<body><main class="wrap">
  <header class="hero">
    <p class="eyebrow">Portfolio analytics · Hyderabad</p>
    <h1>Charging demand, made visible.</h1>
    <p>Explore station performance, charging demand, energy, and estimated revenue in an end-to-end analytics demo.</p>
    <span class="badge">Synthetic practice activity · Jan–Dec 2025</span>
  </header>

  <h2 class="section-title">Network overview <small>(synthetic activity data)</small></h2>
  <section class="kpis" aria-label="Synthetic activity KPIs">
    <article class="card"><div class="kpi-label">Completed sessions</div><div class="kpi-value">{format_number(completed_count)}</div><div class="kpi-note">{format_number(completion_rate, 1)}% of valid synthetic sessions</div></article>
    <article class="card"><div class="kpi-label">Energy delivered</div><div class="kpi-value">{format_number(energy_total / 1000, 1)} MWh</div><div class="kpi-note">Synthetic completed sessions</div></article>
    <article class="card"><div class="kpi-label">Estimated revenue</div><div class="kpi-value">₹{format_number(revenue_total / 100000, 2)} L</div><div class="kpi-note">Generated tariff × generated energy</div></article>
    <article class="card"><div class="kpi-label">Stations represented</div><div class="kpi-value">{active_stations}</div><div class="kpi-note">Synthetic station records</div></article>
    <article class="card"><div class="kpi-label">Average session duration</div><div class="kpi-value">{format_number(average_duration, 1)} min</div><div class="kpi-note">Synthetic completed sessions</div></article>
    <article class="card"><div class="kpi-label">Sessions analyzed</div><div class="kpi-value">{format_number(len(sessions))}</div><div class="kpi-note">Generated for portfolio practice</div></article>
  </section>

  <h2 class="section-title">Demand and revenue patterns <small>(synthetic)</small></h2>
  <section class="charts">
    <article class="card chart-card"><h3>Completed sessions by start hour</h3><img src="figures/demand_by_hour.png" alt="Synthetic line chart of completed sessions by hour"></article>
    <article class="card chart-card"><h3>Estimated revenue by month</h3><img src="figures/monthly_revenue.png" alt="Synthetic monthly estimated revenue line chart"></article>
    <article class="card chart-card chart-wide"><h3>Sessions by Hyderabad location</h3><img src="figures/sessions_by_location.png" alt="Synthetic session counts by location bar chart"></article>
  </section>

  <h2 class="section-title">Location and monthly performance <small>(synthetic)</small></h2>
  <section class="tables">
    <article class="card table-card"><h3>Top locations by completed sessions</h3><div class="table-scroll"><table>
      <thead><tr><th>Location</th><th>Sessions</th><th>Energy (kWh)</th><th>Est. revenue</th></tr></thead><tbody>{location_rows}</tbody>
    </table></div></article>
    <article class="card table-card"><h3>Monthly performance</h3><div class="table-scroll"><table>
      <thead><tr><th>Month</th><th>Sessions</th><th>Est. revenue</th></tr></thead><tbody>{month_rows}</tbody>
    </table></div></article>
  </section>

  <aside class="note"><strong>Data honesty:</strong> session-level KPIs, charts, rankings, and estimated revenue on this page come from synthetic practice data. They are not actual Hyderabad network measurements.</aside>
  <h2 class="section-title">Real public map references</h2>
  <article class="card table-card"><h3>{reference_count} separate OpenStreetMap objects · not joined to synthetic sessions</h3><div class="table-scroll"><table>
    <thead><tr><th>Mapped name or brand</th><th>OSM object</th><th>Coordinates</th><th>Source</th></tr></thead>
    <tbody>{reference_rows}</tbody>
  </table></div></article>
  <aside class="note"><strong>Reference limitations:</strong> OpenStreetMap coverage can be incomplete or out of date. Map records do not confirm current operation. © OpenStreetMap contributors; data available under the <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">ODbL</a>.</aside>
  <footer>Rebuild synthetic datasets and charts with <code>python scripts\\generate_data.py</code> and the EDA notebook; then regenerate this page with <code>python scripts\\build_dashboard.py</code>.</footer>
  <p class="project-credit">A Project Build by Jamalpur Sai Chaithanya</p>
</main></body></html>
"""
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(page, encoding="utf-8")
    DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
    (DEPLOY_DIR / "index.html").write_text(page, encoding="utf-8")
    deployed_figures = DEPLOY_DIR / "figures"
    deployed_figures.mkdir(parents=True, exist_ok=True)
    for image_name in [
        "demand_by_hour.png",
        "monthly_revenue.png",
        "sessions_by_location.png",
    ]:
        image_source = ROOT / "reports" / "figures" / image_name
        if not image_source.is_file():
            raise FileNotFoundError(
                f"Dashboard chart is missing: {image_source}. Run the EDA notebook first."
            )
        (deployed_figures / image_name).write_bytes(image_source.read_bytes())
    print(f"Dashboard saved to {OUTPUT}")
    print(f"Static deployment bundle saved to {DEPLOY_DIR}")


if __name__ == "__main__":
    main()
