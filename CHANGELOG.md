# Changelog

All notable changes to the Zornade - Cadastral Parcels QGIS plugin.
The same changelog (recent versions) is published in `metadata.txt` and shown by
the QGIS Plugin Manager.

## 3.3.1 - 2026-09-30

License note, scope-aware token check, fixed API link.

- **NEW**: license note at the bottom of the dialog, always visible. Explains
  that data comes from the free Zornade API v2 (up to 1,000 requests/hour), that
  internal and professional use is free, and that redistribution or resale
  requires a commercial license. Two links: commercial license page and API
  terms, both with UTM attribution (`qgis-plugin / desktop_app / qgis_plugin_license_note`).
- **FIX**: token validation now calls `parcels/locate`. It verifies the
  `parcels:read` scope and real data access, not just authentication
  (`geocode/search` returns 200 even without results).
- **FIX**: the "Genera token" button now points to app.zornade.com/api with
  standardized UTM parameters (`utm_medium=desktop_app`,
  `utm_campaign=qgis_plugin_api`, legacy `ref` param removed).
- **FIX**: Qt6/QGIS 4 compatibility: `QgsTask.CanCancel` replaced with
  `QgsTask.Flag.CanCancel` (passes the automated Qt6 check on plugins.qgis.org).

## 3.2.0 - 2026-06-08

Parallel downloads and rate-limit handling.

- **NEW**: parcels are now downloaded in parallel via a bounded thread pool
  (30 parcels from ~36s to ~3s).
- **NEW**: "Richieste in parallelo" spin box to set concurrency (1-20, default
  10, persisted).
- **FIX**: HTTP 429 now handled with the server's Retry-After, retrying instead
  of aborting.
- **IMPROVED**: 5xx retries and rate-limit waits are now cooperatively
  cancellable; Cancel stops in-flight workers immediately.
- **CHANGED**: User-Agent updated to ZornadeQGISPlugin/3.2.

## 3.1.0 - 2026-06-29

Three new data sections and a stable map view after download.

- **FIX**: the map canvas is no longer moved after a download; new opt-in
  checkbox "Sposta la vista sulle particelle scaricate" (off by default).
- **NEW**: solar section (JRC PVGIS-SARAH3 photovoltaic potential): availability,
  building count, max kWp, modern/pessimistic annual yield, payback, NPV, CAPEX,
  LCOE, viability class.
- **NEW**: nightlights section (NASA VIIRS Black Marble VNP46A4).
- **NEW**: valuation_history section (OMI semestral series 2015-2025).
- 113 attribute fields mapped from the API v2.4 response, all 20 data sections
  covered.
- **CLEANUP**: removed the embedded Supabase anon JWT and the Authorization
  Bearer header; only the x-api-key header is required.

## 3.0.0 - 2026-06-08

Complete API v2.4 alignment: 90+ attribute fields, 17 data sections.

- **CRITICAL FIX**: mandatory Authorization Bearer header (later removed in 3.1.0).
- **CRITICAL FIX**: search endpoint now uses the correct v2.4 params (comune,
  foglio, label, sezione).
- **CRITICAL FIX**: parcel detail now sends include=all to receive all sections.
- **NEW**: terrain, population, buildings, economics, demographics, land use,
  coastal erosion, cultural heritage, POI and addresses sections.
- **IMPROVED**: subsidence now includes all 7 fields, valuation includes
  fascia/condition/entry count, cadastral search uses fuzzy municipality name,
  results table shows the Foglio column.

## 2.2.1 - 2026-04-14

- **FIX**: explicit attribute type casting before setAttribute.

## 2.2.0 - 2026-04-14

- **FIX**: empty layer after download due to reserved field name conflict,
  field "fid" renamed to "parcel_id".

## 2.1.0 - 2026-04-14

- Complete data model rewrite: 35 fields (was 15), CORINE Land Cover categorized
  renderer, seismic zone renderer, subsidence risk renderer, OMI valuation,
  subsidence analysis (velocity, risk class, direction), adaptive quadtree bbox
  search, robust GeoJSON parsing via OGR, retry with exponential backoff, max
  results raised to 500.

## 2.0.1 - 2026-04-14

- Multi-point bbox search (3x3 grid, deduplicated), download via QgsTask,
  QgsMessageLog logging, English metadata.

## 2.0.0 - 2026-04-14

- Complete rewrite for API v2: native Qt6 interface, no RapidAPI required, search
  by coordinates/map canvas bbox/cadastral reference, map picking, categorized
  sketching, async download with progress bar, secure token management with
  in-app verification.

## 1.0.0 - 2026-04-14

- Initial release (deprecated).
