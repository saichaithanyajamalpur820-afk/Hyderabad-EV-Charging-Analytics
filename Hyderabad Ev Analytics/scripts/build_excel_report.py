"""Export an Excel workbook for the real mapped-site inventory and its limits."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "reference" / "charging_sites_openstreetmap.csv"
OUTPUT = ROOT / "reports" / "hyderabad_charging_sites.xlsx"


def main() -> None:
    sites = pd.read_csv(SOURCE)
    for column in ["name", "brand", "operator", "network", "access", "capacity"]:
        sites[column] = sites[column].fillna("").astype(str).str.strip()

    sites["display_name"] = sites["name"].where(sites["name"].ne(""), sites["brand"])
    sites.loc[sites["display_name"].eq(""), "display_name"] = "Name not mapped"
    completeness = pd.DataFrame(
        [
            {"Attribute": column, "Populated records": int(sites[column].ne("").sum())}
            for column in ["name", "brand", "operator", "network", "access", "capacity"]
        ]
    )
    completeness["Missing records"] = len(sites) - completeness["Populated records"]
    completeness["Coverage (%)"] = (
        completeness["Populated records"] / len(sites) * 100
    ).round(1)

    data_dictionary = pd.DataFrame(
        [
            ("osm_type", "OpenStreetMap object type: node, way, or relation."),
            ("osm_id", "OpenStreetMap object identifier."),
            ("name / brand / operator / network", "Values explicitly mapped in OSM; blank means not tagged."),
            ("latitude / longitude", "Mapped point coordinates; way/relation use the OSM center point."),
            ("access", "OSM access tag, when present; not a verified operating policy."),
            ("capacity", "OSM capacity tag, when present; not independently verified."),
            ("snapshot_utc", "Timestamp reported by the Overpass/OSM data snapshot."),
            ("source_url", "Direct source object record."),
        ],
        columns=["Field", "Meaning and limitation"],
    )
    readme = pd.DataFrame(
        [
            ("Purpose", "Audit publicly mapped EV charging-site objects for the Hyderabad query area."),
            ("Source", "OpenStreetMap via Overpass API; query amenity=charging_station."),
            ("Snapshot", str(sites["snapshot_utc"].iloc[0]) if len(sites) else "No records"),
            ("Mapped objects", len(sites)),
            ("Important limitation", "OSM coverage may be incomplete; records do not confirm current operation."),
            ("Not available here", "No real session, kWh, utilization, queue, outage, or revenue data."),
            ("License", "Open Database License (ODbL); credit OpenStreetMap contributors."),
        ],
        columns=["Item", "Details"],
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(OUTPUT, engine="openpyxl") as writer:
        readme.to_excel(writer, sheet_name="Read me", index=False)
        sites.to_excel(writer, sheet_name="Site inventory", index=False)
        completeness.to_excel(writer, sheet_name="Tag completeness", index=False)
        data_dictionary.to_excel(writer, sheet_name="Data dictionary", index=False)

        for worksheet in writer.book.worksheets:
            worksheet.freeze_panes = "A2"
            worksheet.auto_filter.ref = worksheet.dimensions
            for cell in worksheet[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill("solid", fgColor="087E78")
                cell.alignment = Alignment(vertical="center", wrap_text=True)
            for column_cells in worksheet.columns:
                letter = get_column_letter(column_cells[0].column)
                max_length = max(
                    len(str(cell.value or ""))
                    for cell in column_cells
                )
                worksheet.column_dimensions[letter].width = min(max(max_length + 2, 12), 55)
            worksheet.row_dimensions[1].height = 30

    print(f"Saved Excel workbook with {len(sites)} mapped objects: {OUTPUT}")


if __name__ == "__main__":
    main()
