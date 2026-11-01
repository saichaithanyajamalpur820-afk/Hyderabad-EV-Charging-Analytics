"""Generate deterministic synthetic EV charging activity for portfolio practice."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


SEED = 20261101
START_DATE = pd.Timestamp("2025-01-01")
END_DATE = pd.Timestamp("2025-12-31 23:59:59")
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

LOCATION_CENTERS = {
    "Gachibowli": (17.4401, 78.3489),
    "Madhapur": (17.4483, 78.3915),
    "HITEC City": (17.4435, 78.3772),
    "Kondapur": (17.4604, 78.3569),
    "Banjara Hills": (17.4126, 78.4482),
    "Jubilee Hills": (17.4310, 78.4070),
    "Kukatpally": (17.4948, 78.3996),
    "Secunderabad": (17.4399, 78.4983),
    "LB Nagar": (17.3457, 78.5522),
    "Shamshabad": (17.2403, 78.4294),
}


def build_stations(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    number = 1
    for location, (latitude, longitude) in LOCATION_CENTERS.items():
        for local_index in range(1, 4):
            rows.append(
                {
                    "station_id": f"ST{number:03d}",
                    "station_name": f"{location} Charging Hub {local_index}",
                    "location": location,
                    "city": "Hyderabad",
                    "latitude": round(latitude + rng.normal(0, 0.006), 6),
                    "longitude": round(longitude + rng.normal(0, 0.006), 6),
                    "opening_date": (
                        START_DATE - pd.Timedelta(days=int(rng.integers(30, 900)))
                    ).date().isoformat(),
                    "station_type": rng.choice(
                        ["Public", "Retail", "Highway"], p=[0.60, 0.30, 0.10]
                    ),
                }
            )
            number += 1
    return pd.DataFrame(rows)


def build_chargers(
    stations: pd.DataFrame, rng: np.random.Generator
) -> pd.DataFrame:
    rows = []
    number = 1
    charger_specs = [
        ("AC", 22, "Type 2"),
        ("DC Fast", 50, "CCS2"),
        ("DC Fast", 120, "CCS2"),
    ]
    for station_id in stations["station_id"]:
        for charger_type, power_kw, connector in charger_specs:
            rows.append(
                {
                    "charger_id": f"CH{number:03d}",
                    "station_id": station_id,
                    "charger_type": charger_type,
                    "power_kw": power_kw,
                    "connector_type": connector,
                    "charger_status": rng.choice(
                        ["Operational", "Maintenance"], p=[0.95, 0.05]
                    ),
                }
            )
            number += 1
    return pd.DataFrame(rows)


def build_customers(rng: np.random.Generator) -> pd.DataFrame:
    count = 500
    offsets = rng.integers(0, 1100, size=count)
    return pd.DataFrame(
        {
            "customer_id": [f"CU{number:04d}" for number in range(1, count + 1)],
            "signup_date": [
                (START_DATE - pd.Timedelta(days=int(offset))).date().isoformat()
                for offset in offsets
            ],
            "vehicle_model": rng.choice(
                ["Tata Nexon EV", "MG ZS EV", "BYD Atto 3", "Hyundai Kona", "Other"],
                size=count,
                p=[0.35, 0.22, 0.17, 0.12, 0.14],
            ),
            "vehicle_segment": rng.choice(
                ["Hatchback", "SUV", "Sedan"], size=count, p=[0.20, 0.65, 0.15]
            ),
            "preferred_payment": rng.choice(
                ["UPI", "Credit Card", "Wallet", "RFID"],
                size=count,
                p=[0.48, 0.23, 0.17, 0.12],
            ),
        }
    )


def build_sessions(
    stations: pd.DataFrame,
    chargers: pd.DataFrame,
    customers: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    count = 15_000
    dates = pd.date_range(START_DATE.normalize(), END_DATE.normalize(), freq="D")
    hours = np.arange(24)
    hour_weights = (
        0.25
        + 1.7 * np.exp(-((hours - 8) ** 2) / 8)
        + 1.9 * np.exp(-((hours - 18) ** 2) / 12)
    )
    date_weights = np.ones(len(dates), dtype=float)
    date_weights[dates.dayofweek >= 5] *= 1.15
    date_weights[dates.month == 12] *= 1.08
    date_weights /= date_weights.sum()

    station_weights = np.array(
        [
            1.35 if location in {"Gachibowli", "Madhapur", "HITEC City"} else 1.0
            for location in stations["location"]
        ],
        dtype=float,
    )
    station_weights /= station_weights.sum()
    station_ids = rng.choice(stations["station_id"], size=count, p=station_weights)
    charger_lookup = {
        station_id: group["charger_id"].to_numpy()
        for station_id, group in chargers.groupby("station_id", sort=False)
    }
    charger_ids = np.array(
        [rng.choice(charger_lookup[station_id]) for station_id in station_ids]
    )
    charger_power = chargers.set_index("charger_id")["power_kw"]
    power = np.array([charger_power[charger_id] for charger_id in charger_ids])

    date_indices = rng.choice(len(dates), size=count, p=date_weights)
    sampled_hours = rng.choice(hours, size=count, p=hour_weights / hour_weights.sum())
    starts = (
        dates.take(date_indices)
        + pd.to_timedelta(sampled_hours, unit="h")
        + pd.to_timedelta(rng.integers(0, 60, size=count), unit="m")
        + pd.to_timedelta(rng.integers(0, 60, size=count), unit="s")
    )
    duration = np.clip(rng.lognormal(mean=3.85, sigma=0.48, size=count), 10, 180)
    efficiency = rng.uniform(0.78, 0.93, size=count)
    battery_limit = rng.uniform(24, 72, size=count)
    energy = np.minimum(power * duration / 60 * efficiency, battery_limit)
    status = rng.choice(
        ["Completed", "Interrupted", "Failed"], size=count, p=[0.93, 0.05, 0.02]
    )
    failed = status == "Failed"
    interrupted = status == "Interrupted"
    energy[failed] = rng.uniform(0, 2, size=failed.sum())
    energy[interrupted] *= rng.uniform(0.15, 0.75, size=interrupted.sum())
    tariff = rng.choice(
        [12.0, 14.0, 16.0, 18.0], size=count, p=[0.15, 0.35, 0.35, 0.15]
    )
    payment = rng.choice(
        ["UPI", "Credit Card", "Wallet", "RFID"],
        size=count,
        p=[0.48, 0.23, 0.17, 0.12],
    )

    sessions = pd.DataFrame(
        {
            "session_id": [f"SE{number:05d}" for number in range(1, count + 1)],
            "station_id": station_ids,
            "charger_id": charger_ids,
            "customer_id": rng.choice(customers["customer_id"], size=count),
            "session_start": starts,
            "session_end": starts + pd.to_timedelta(duration, unit="m"),
            "duration_minutes": np.round(duration, 2),
            "energy_kwh": np.round(energy, 2),
            "tariff_inr_per_kwh": tariff,
            "revenue_inr": np.round(energy * tariff, 2),
            "session_status": status,
            "payment_method": payment,
        }
    )
    missing_payment = rng.choice(sessions.index, size=75, replace=False)
    sessions.loc[missing_payment, "payment_method"] = pd.NA
    return sessions


def build_maintenance(
    chargers: pd.DataFrame, rng: np.random.Generator
) -> pd.DataFrame:
    count = 500
    start = START_DATE + pd.to_timedelta(
        rng.integers(0, 365 * 24, size=count), unit="h"
    )
    return pd.DataFrame(
        {
            "maintenance_id": [
                f"MA{number:04d}" for number in range(1, count + 1)
            ],
            "charger_id": rng.choice(chargers["charger_id"], size=count),
            "maintenance_date": start,
            "maintenance_type": rng.choice(
                [
                    "Connector Inspection",
                    "Power Module Repair",
                    "Software Update",
                    "Cable Replacement",
                    "Preventive Service",
                ],
                size=count,
            ),
            "severity": rng.choice(
                ["Low", "Medium", "High"], size=count, p=[0.45, 0.40, 0.15]
            ),
            "downtime_hours": np.round(
                np.clip(
                    rng.lognormal(mean=1.0, sigma=0.7, size=count), 0.5, 48
                ),
                2,
            ),
            "maintenance_cost_inr": np.round(
                rng.lognormal(mean=7.8, sigma=0.65, size=count), 2
            ),
        }
    )


def main() -> None:
    rng = np.random.default_rng(SEED)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stations = build_stations(rng)
    chargers = build_chargers(stations, rng)
    customers = build_customers(rng)
    datasets = {
        "stations.csv": stations,
        "chargers.csv": chargers,
        "customers.csv": customers,
        "charging_sessions.csv": build_sessions(stations, chargers, customers, rng),
        "maintenance.csv": build_maintenance(chargers, rng),
    }
    for filename, dataframe in datasets.items():
        dataframe.to_csv(OUTPUT_DIR / filename, index=False)
        print(f"{filename}: {len(dataframe):,} rows")
    print(f"Synthetic practice data saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
