"""Refresh the Hyderabad charging-site snapshot from OpenStreetMap Overpass."""

from __future__ import annotations

import csv
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "data" / "reference"
CSV_PATH = REFERENCE_DIR / "charging_sites_openstreetmap.csv"
JSON_PATH = REFERENCE_DIR / "charging_sites_openstreetmap.json"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
BOUNDING_BOX = (17.15, 78.15, 17.65, 78.70)
FIELDS = [
    "osm_type",
    "osm_id",
    "name",
    "brand",
    "operator",
    "network",
    "latitude",
    "longitude",
    "access",
    "capacity",
    "source_url",
    "snapshot_utc",
    "license",
]


def build_query() -> str:
    south, west, north, east = BOUNDING_BOX
    bounds = f"{south},{west},{north},{east}"
    return (
        "[out:json][timeout:60];("
        f"node[amenity=charging_station]({bounds});"
        f"way[amenity=charging_station]({bounds});"
        f"relation[amenity=charging_station]({bounds});"
        ");out center tags;"
    )


def get_site_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    snapshot = payload.get("osm3s", {}).get("timestamp_osm_base")
    if not snapshot:
        snapshot = datetime.now(timezone.utc).isoformat(timespec="seconds")
    copyright_text = payload.get("osm3s", {}).get("copyright", "")
    rows = []

    for element in payload.get("elements", []):
        tags = element.get("tags", {})
        coordinates = element.get("center", element)
        latitude = coordinates.get("lat")
        longitude = coordinates.get("lon")
        if latitude is None or longitude is None:
            continue

        osm_type = element["type"]
        osm_id = element["id"]
        rows.append(
            {
                "osm_type": osm_type,
                "osm_id": osm_id,
                "name": tags.get("name", ""),
                "brand": tags.get("brand", ""),
                "operator": tags.get("operator", ""),
                "network": tags.get("network", ""),
                "latitude": latitude,
                "longitude": longitude,
                "access": tags.get("access", ""),
                "capacity": tags.get("capacity", ""),
                "source_url": f"https://www.openstreetmap.org/{osm_type}/{osm_id}",
                "snapshot_utc": snapshot,
                "license": "Open Database License (ODbL)",
            }
        )

    payload["project_attribution"] = copyright_text
    return rows


def fetch_payload() -> dict[str, Any]:
    query = urllib.parse.urlencode({"data": build_query()})
    request = urllib.request.Request(
        f"{OVERPASS_URL}?{query}",
        headers={
            "User-Agent": "HyderabadEVAnalyticsPortfolio/1.0 (public OSM data)",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            payload = json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError(
            "Could not refresh data from the OpenStreetMap Overpass API. "
            "The last checked-in snapshot was left unchanged."
        ) from error

    if payload.get("remark"):
        raise RuntimeError(f"Overpass returned an incomplete result: {payload['remark']}")
    if "elements" not in payload or not isinstance(payload["elements"], list):
        raise RuntimeError("Overpass response is missing its elements list.")
    return payload


def main() -> None:
    payload = fetch_payload()
    rows = get_site_rows(payload)
    if not rows:
        raise RuntimeError(
            "The query returned no mappable charging-site objects; "
            "the existing snapshot was left unchanged."
        )

    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    with CSV_PATH.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    snapshot = payload.get("osm3s", {}).get("timestamp_osm_base", "unknown")
    print(f"Saved {len(rows)} mapped charging-site objects to {CSV_PATH}")
    print(f"OpenStreetMap data snapshot: {snapshot}")
    print("Map data © OpenStreetMap contributors; available under the ODbL.")


if __name__ == "__main__":
    main()
