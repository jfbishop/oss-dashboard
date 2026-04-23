# Data Dictionary

## dashboard_data.js

### `schools` array

| Field | Type | Description |
|---|---|---|
| `t` | string | `"case"` (OSS school) or `"ctrl"` (matched control) |
| `g` | number | Match group ID (1–57); case and control share the same group number |
| `n` | string | School display name |
| `en` | string | DOE entity name (used as join key) |
| `org` | string | `"DOE"` or `"Charter"` |
| `gc` | string | Grade category (e.g. `"Elementary"`, `"High School"`) |
| `ag` | string | Active grades (e.g. `"K,1,2,3,4,5"`) |
| `q` | string | % Hispanic quartile: `"Q1"` (≤29%) through `"Q4"` (>75%) |
| `pg` | boolean | Has playground/outdoor space |
| `addr` | string | Street address |
| `boro` | string | Borough / city |
| `lat` / `lon` | number | WGS84 coordinates |
| `enroll` | number | Total enrollment (sum of num_female + num_male + num_nonbinary) |
| `ph` | number | % Hispanic |
| `pb` | number | % Black |
| `pw` | number | % White |
| `pa` | number | % Asian |
| `pai` | number | % American Indian |
| `pm_r` | number | % Multiracial |
| `pf` | number | % Female |
| `pml` | number | % Male |
| `pe` | number | % English Language Learners |
| `ps` | number | % Students with Disabilities |
| `pec` | number | % Economically Disadvantaged |
| `segs` | array | List of segment `object_id`s associated with this school |
| `yrs` | number\|null | Years in OSS program (null = pending data from city) |

### `excluded` array

| Field | Type | Description |
|---|---|---|
| `t` | string | Always `"excl"` |
| `n` | string | School name |
| `addr` | string | Street address |
| `lat` / `lon` | number | WGS84 coordinates (derived from segment centroid) |
| `segs` | array | Associated segment `object_id`s |

### `segments` array

| Field | Type | Description |
|---|---|---|
| `id` | number | `object_id` from NYC DOE OSS data |
| `lines` | array | GeoJSON-style coordinate arrays `[[lon,lat],...]` in WGS84 |
| `on_street` | string | Street name |
| `from_street` | string | Cross street (start) |
| `to_street` | string | Cross street (end) |
| `borough` | string | Borough |
| `inst_type` | string | `"PUBLIC SCHOOLS"` or `"NON-PUBLIC SCHOOLS"` |
| `has_match` | boolean | Whether this segment matched to a school in our analysis |
| `school_name` | string | Associated school name |
| `pnames` | array | DOE popular name(s) for the associated school(s) |
| `sched` | array | Schedule entries (see below) |

#### `sched` entries

| Field | Type | Description |
|---|---|---|
| `days` | string | Days open, e.g. `"Mon-Fri"`, `"Wed, Fri"` |
| `cat` | string | `"all_day"`, `"middle_of_day"`, `"drop_off"`, or `"pick_up"` |
| `open` | string | Open time, e.g. `"7:30 AM"` |
| `close` | string | Close time, e.g. `"3:00 PM"` |
| `notes` | string | Any data quality notes |

---

## oss_timing_clean.csv

Clean version of the OSS street timing data used to build `dashboard_data.js`.

| Column | Description |
|---|---|
| `object_id` | Joins to `segments[].id` |
| `org_name` | Organization/school name |
| `days` | Days the street is closed to traffic |
| `time_category` | One of: `all_day`, `middle_of_day`, `drop_off`, `pick_up` |
| `open_time` | Street open time |
| `close_time` | Street close time |
| `notes` | Data quality notes (e.g. corrected clerical errors) |
