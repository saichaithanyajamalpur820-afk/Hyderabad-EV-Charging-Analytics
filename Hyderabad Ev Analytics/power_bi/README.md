# Power BI setup — public charging-site inventory

This report is limited to the public OpenStreetMap inventory snapshot. It must
not imply utilization, real operating status, revenue, or demand because those
fields are not present in the source.

## Load the data

1. In Power BI Desktop, select **Get data → Text/CSV**.
2. Load `data/reference/charging_sites_openstreetmap.csv` as `ChargingSites`.
3. Set `latitude` and `longitude` to **Decimal number**, `osm_id` to **Whole
   number**, and `snapshot_utc` to **Date/time**.
4. Create a calculated column:

```DAX
Display Name =
VAR SiteName = TRIM ( COALESCE ( ChargingSites[name], "" ) )
VAR SiteBrand = TRIM ( COALESCE ( ChargingSites[brand], "" ) )
RETURN
    SWITCH (
        TRUE (),
        SiteName <> "", SiteName,
        SiteBrand <> "", SiteBrand,
        "Name not mapped"
    )
```

## Measures

```DAX
Mapped OSM Objects = COUNTROWS ( ChargingSites )

Objects With Brand =
COUNTROWS (
    FILTER ( ChargingSites, LEN ( TRIM ( COALESCE ( ChargingSites[brand], "" ) ) ) > 0 )
)

Objects With Access Tag =
COUNTROWS (
    FILTER ( ChargingSites, LEN ( TRIM ( COALESCE ( ChargingSites[access], "" ) ) ) > 0 )
)

Objects With Capacity Tag =
COUNTROWS (
    FILTER ( ChargingSites, LEN ( TRIM ( COALESCE ( ChargingSites[capacity], "" ) ) ) > 0 )
)
```

## Suggested page

- KPI cards: mapped OSM objects, objects with brand, access tag, capacity tag.
- Map visual: latitude and longitude, with `Display Name` as the tooltip.
- Table: name, brand, access, capacity, coordinates, snapshot, source URL.
- Slicers: access, brand, OSM object type.
- Visible note: “OSM inventory coverage is incomplete; mapped presence does not
  verify current operation. No session/demand data is available.”

Credit © OpenStreetMap contributors; data available under the ODbL.
