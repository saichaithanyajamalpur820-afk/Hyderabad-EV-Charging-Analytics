-- SQLite-compatible analysis of the real OpenStreetMap inventory snapshot.
-- Load data/reference/charging_sites_openstreetmap.csv as charging_sites first.

-- 1. Mapped objects, not a confirmed count of all physical stations.
SELECT COUNT(*) AS mapped_osm_objects
FROM charging_sites;

-- 2. Source-tag completeness.
SELECT
    COUNT(*) AS mapped_objects,
    SUM(CASE WHEN NULLIF(TRIM(name), '') IS NOT NULL THEN 1 ELSE 0 END) AS with_name,
    SUM(CASE WHEN NULLIF(TRIM(brand), '') IS NOT NULL THEN 1 ELSE 0 END) AS with_brand,
    SUM(CASE WHEN NULLIF(TRIM(access), '') IS NOT NULL THEN 1 ELSE 0 END) AS with_access_tag,
    SUM(CASE WHEN NULLIF(TRIM(capacity), '') IS NOT NULL THEN 1 ELSE 0 END) AS with_capacity_tag
FROM charging_sites;

-- 3. Mapped access tags; an empty tag means unknown, not unrestricted.
SELECT
    COALESCE(NULLIF(TRIM(access), ''), 'Not mapped') AS access_tag,
    COUNT(*) AS mapped_objects
FROM charging_sites
GROUP BY COALESCE(NULLIF(TRIM(access), ''), 'Not mapped')
ORDER BY mapped_objects DESC;

-- 4. Review each source object and open its public OSM record.
SELECT
    osm_type,
    osm_id,
    COALESCE(NULLIF(TRIM(name), ''), NULLIF(TRIM(brand), ''), 'Name not mapped') AS display_name,
    latitude,
    longitude,
    NULLIF(TRIM(access), '') AS access_tag,
    NULLIF(TRIM(capacity), '') AS mapped_capacity,
    source_url,
    snapshot_utc
FROM charging_sites
ORDER BY display_name, osm_type, osm_id;

-- 5. Duplicate coordinates can flag objects needing manual map review.
SELECT latitude, longitude, COUNT(*) AS objects_at_coordinate
FROM charging_sites
GROUP BY latitude, longitude
HAVING COUNT(*) > 1
ORDER BY objects_at_coordinate DESC;
