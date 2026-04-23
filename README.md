# NYC Open Streets for Schools (OSS) · Spatial Equity Dashboard

An interactive map dashboard presenting findings from a spatial equity analysis of schools in the NYC Open Streets for Schools program.

**Live dashboard:** https://oss-dashboard-psi.vercel.app/

---

## What this is

The Open Streets for Schools (OSS) program closes street segments adjacent to participating schools during school hours, creating car-free outdoor space for students. This dashboard visualizes a matched case-control analysis comparing **57 OSS schools** (cases) to **57 matched control schools**, along with 12 excluded non-public schools and all associated street segments.

**Matching criteria:** grade level + % Hispanic quartile (57 matched pairs).

---

## Repo structure

```
oss-dashboard/
├── index.html                  # Main dashboard (Leaflet.js)
├── data/
├── dashboard_data.js           # All map data (schools, segments, schedules)
│   ├── oss_timing_clean.csv    # Source timing data for reference
│   └── update_data.py          # Script to regenerate dashboard_data.js
├── docs/
│   └── data_dictionary.md      # Field definitions
├── README.md
└── .gitignore
```

---

## How to view locally

Open `index.html` directly in Chrome or Firefox — no server needed.

---

## How to update the data

All map data lives in `dashboard_data.js` (repo root, next to `index.html`). When source data changes, regenerate it by running:

```bash
cd data
python update_data.py
```

**Before running**, edit the file paths at the top of `update_data.py` to point to your current CSV files. The script expects:

| File | Description |
|---|---|
| `oss_matched_v1_YYYYMMDD.csv` | Matched case/control schools with demographics and lat/lon |
| `oss_segments_final.csv` | OSS street segments with WKT geometry (NY State Plane) |
| `oss_segments_treated.csv` | Same segments with WGS84 coordinates |
| `oss_timing_clean.csv` | Street schedule data (already in `data/`) |

### Adding years-in-program data
Once received from the city, add a `years_in_program` column to your matched CSV (joined on `sed_code` or `entity_name`) and re-run `update_data.py`. The script already reads `'yrs'` from that column — just change the `None` default to `int(r['years_in_program'])`.

### Adding neighborhood / ACS data
In `index.html`, find `function populateNeighborhood()` and replace the `null` placeholder values with real ACS data. The function already receives the selected school and its matched partner.

### Adding playground polygons
1. Draw polygons at [geojson.io](https://geojson.io) using satellite view
2. Save as `data/playgrounds.geojson`
3. In `index.html`, find the `refreshPlaygrounds()` function and replace the circle-based placeholder with a Leaflet GeoJSON layer loading from that file

---

## Data sources

| Data | Source |
|---|---|
| OSS school list & street segments | NYC DOE / Open Plans |
| School demographics | NYC DOE Open Data (2024–25) |
| Street geometries | NYC Open Data (LION street centerline, EPSG:2263) |
| Base map | CartoDB Light (© OpenStreetMap contributors, © CARTO) |
| School map pin icon | [The Noun Project #1661311](https://thenounproject.com/icon/school-map-pin-1661311/) by The Noun Project (CC BY 3.0) |

---

## Dependencies

- [Leaflet.js 1.9.4](https://leafletjs.com/) — loaded from CDN, no install needed
- [DM Sans + Fraunces](https://fonts.google.com/) — loaded from Google Fonts
- Python 3 + pandas — only needed to regenerate `dashboard_data.js`

---

## Pending data / placeholders

The following appear as "N/A" or "Pending" in the dashboard and will be populated as data becomes available:

- **Years in program** — pending data from NYC DOE / Open Plans
- **Neighborhood characteristics** (poverty %, median income, child health) — pending ACS integration
- **Playground polygons** — pending manual digitization via geojson.io
- **Street attributes** (length, lanes, speed limit, bike lane, traffic calming) — pending data from NYC DOT

---

## Authors

**Kathryn (Katie) G. Burford**, PhD 
Post Doctoral Scholar 
[Built Environment and Health Research Group](https://beh.columbia.edu/) 
Columbia University Mailman School of Public Health

**Anna Carl**
MS Candidate, Urban Planning
Columbia University Graduate School of Architecture, Planning and Preservation

**Juliet Bishop**
MA Candidate, Quantitative Methods in the Social Sciences  
Columbia University Graduate School of Arts and Sciences

---

## License

Code: MIT  
Data: See individual source licenses above