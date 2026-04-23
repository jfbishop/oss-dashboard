"""
update_data.py
==============
Regenerates data/dashboard_data.js from source CSV files.
Run this whenever the underlying school or segment data changes.

Usage:
    python data/update_data.py

Requirements:
    pip install pandas

Input files (edit SOURCE paths below if yours differ):
    - oss_matched_v1_YYYYMMDD.csv   (matched case/control schools)
    - oss_segments_final.csv        (OSS street segments, WKT geometry)
    - oss_timing_clean.csv          (street schedule data — this file)

Output:
    data/dashboard_data.js          (overwrites in place)
"""

import pandas as pd
import re
import math
import json
import os
from pathlib import Path

# ── Edit these paths to point to your source files ───────────────────────────
HERE = Path(__file__).parent
MATCHED_CSV  = HERE / "oss_matched_v1_20260420.csv"        # update filename when refreshed
SEGMENTS_CSV = HERE / "oss_segments_final.csv"
TIMING_CSV   = HERE / "oss_timing_clean.csv"
SEGMENTS_TREATED_CSV = HERE / "oss_segments_treated.csv"   # has WGS84 coords
OUTPUT_JS    = HERE.parent / "dashboard_data.js"  # root of repo, next to index.html
# ─────────────────────────────────────────────────────────────────────────────


def sp2263_to_wgs84(x_ft, y_ft):
    """Convert NY State Plane (EPSG:2263, US survey feet) to WGS84 lat/lon."""
    a = 6378137.0; f = 1/298.257222101; b = a*(1-f)
    e2 = 1-(b/a)**2; e = math.sqrt(e2)
    US_FT = 0.3048006096012192
    x = x_ft * US_FT; y = y_ft * US_FT
    lat1 = math.radians(40+40/60); lat2 = math.radians(41+2.5/60)
    lat0 = math.radians(40+10/60); lon0 = math.radians(-74); FE = 300000.0
    def mf(l): s=math.sin(l); return math.cos(l)/math.sqrt(1-e2*s**2)
    def tf(l): s=math.sin(l); return math.tan(math.pi/4-l/2)/((1-e*s)/(1+e*s))**(e/2)
    m1=mf(lat1); m2=mf(lat2); t0=tf(lat0); t1=tf(lat1); t2=tf(lat2)
    n=(math.log(m1)-math.log(m2))/(math.log(t1)-math.log(t2))
    F=m1/(n*t1**n); rho0=a*F*t0**n
    E=x-FE; Nv=rho0-y; rho=math.copysign(math.sqrt(E**2+Nv**2),n)
    theta=math.atan2(E,Nv); t=(rho/(a*F))**(1/n)
    lat=math.pi/2-2*math.atan(t)
    for _ in range(10):
        s=math.sin(lat); lat=math.pi/2-2*math.atan(t*((1-e*s)/(1+e*s))**(e/2))
    return round(math.degrees(lat),6), round(math.degrees(theta/n+lon0),6)


def parse_wkt_wgs84(wkt):
    """Parse MULTILINESTRING WKT (WGS84) into list of coordinate arrays."""
    lines = []
    for line_str in re.findall(r'\(([^()]+)\)', wkt):
        coords = []
        for m in re.finditer(r'(-?[\d.]+)\s+([\d.]+)', line_str):
            lon, lat = float(m.group(1)), float(m.group(2))
            if -74.4 < lon < -73.4 and 40.3 < lat < 41.1:
                coords.append([round(lon,6), round(lat,6)])
        if coords:
            lines.append(coords)
    return lines


def ns(v, cast=None):
    """Null-safe cast — returns None for NaN/missing values."""
    if v is None: return None
    try:
        if math.isnan(float(v)): return None
    except: pass
    if cast:
        try: return cast(v)
        except: return None
    return v


def build_schools(matched, segments_orig, seg_info):
    schools = []
    for _, r in matched.iterrows():
        en = str(r['entity_name']).strip()
        is_case = int(r['case_or_ctrl']) == 1
        obj_ids = [oid for oid, info in seg_info.items() if en in info['pnames']]
        nf = ns(r['num_female'], float) or 0
        nm = ns(r['num_male'],   float) or 0
        nnb = ns(r['num_nonbinary'], float) or 0
        name = str(r['name']).strip() if pd.notna(r['name']) else en
        schools.append({
            't': 'case' if is_case else 'ctrl',
            'g': int(r['match_group']),
            'n': name,
            'en': en,
            'org': str(r['org_type']).strip() if pd.notna(r['org_type']) else '',
            'gc': str(r['grade_category']).strip() if pd.notna(r['grade_category']) else '',
            'ag': str(r['active_grades']).strip() if pd.notna(r['active_grades']) else '',
            'q':  str(r['hisp_quartile']).strip() if pd.notna(r['hisp_quartile']) else '',
            'pg': int(r['playground_status'])==1 if pd.notna(r['playground_status']) else False,
            'addr': str(r['address_line_1']).strip() if pd.notna(r['address_line_1']) else '',
            'boro': str(r['city']).strip() if pd.notna(r['city']) else '',
            'lat': round(float(r['lat']), 6),
            'lon': round(float(r['lon']), 6),
            'enroll': int(nf + nm + nnb),
            'ph':  ns(r['per_hisp'],  float),
            'pb':  ns(r['per_black'], float),
            'pw':  ns(r['per_white'], float),
            'pa':  ns(r['per_asian'], float),
            'pai': ns(r['per_am_ind'],float),
            'pm_r':ns(r['per_multi'], float),
            'pf':  ns(r['per_female'],float),
            'pml': ns(r['per_male'],  float),
            'pe':  ns(r['per_ell'],   float),
            'ps':  ns(r['per_swd'],   float),
            'pec': ns(r['per_ecdis'], float),
            'segs': obj_ids,
            'yrs': None,  # ← update with years-in-program data from city
        })
    return schools


def build_excluded(segments_orig):
    excluded = []
    nonpub = segments_orig[
        segments_orig['inst_type'] == 'NON-PUBLIC SCHOOLS'
    ].drop_duplicates('school_name')
    for _, r in nonpub.iterrows():
        oid = int(r['object_id'])
        wkt = str(r['the_geom_wkt'])
        cr = re.findall(r'([\d.]+)\s+([\d.]+)', wkt)
        if cr:
            xs = [float(c[0]) for c in cr]
            ys = [float(c[1]) for c in cr]
            lat, lon = sp2263_to_wgs84(sum(xs)/len(xs), sum(ys)/len(ys))
            excluded.append({
                't': 'excl',
                'n': str(r['school_name']).strip(),
                'addr': str(r['school_address']).strip() if pd.notna(r['school_address']) else '',
                'lat': lat, 'lon': lon,
                'segs': [oid],
            })
    return excluded


def build_segments(segments_treated, seg_info, timing_lkp):
    segs = []
    for _, r in segments_treated.iterrows():
        oid = int(r['Object ID'])
        info = seg_info.get(oid, {})
        lines = parse_wkt_wgs84(str(r['The_Geom']))
        sched = timing_lkp.get(oid, [])
        segs.append({
            'id': oid,
            'lines': lines,
            'on_street':   str(r['Approved On Street'])   if pd.notna(r['Approved On Street'])   else '',
            'from_street': str(r['Approved From Street']) if pd.notna(r['Approved From Street']) else '',
            'to_street':   str(r['Approved To Street'])   if pd.notna(r['Approved To Street'])   else '',
            'borough':     str(r['Borough Name'])         if pd.notna(r['Borough Name'])         else '',
            'inst_type':   info.get('inst_type', ''),
            'has_match':   info.get('has_match', False),
            'school_name': info.get('school_name', ''),
            'pnames':      info.get('pnames', []),
            'sched':       sched,
        })
    return segs


def main():
    print("Loading CSVs...")
    matched          = pd.read_csv(MATCHED_CSV,          encoding='latin1')
    segments_orig    = pd.read_csv(SEGMENTS_CSV,         encoding='latin1')
    segments_treated = pd.read_csv(SEGMENTS_TREATED_CSV, encoding='latin1')
    timing           = pd.read_csv(TIMING_CSV,           encoding='utf-8')

    # Build segment info lookup (orig file has school linkage)
    seg_info = {}
    for _, r in segments_orig.iterrows():
        oid = int(r['object_id'])
        pn  = str(r['popular_name']).strip() if pd.notna(r['popular_name']) else None
        if oid not in seg_info:
            seg_info[oid] = {
                'pnames':      [],
                'inst_type':   str(r['inst_type']).strip()    if pd.notna(r['inst_type'])    else '',
                'has_match':   bool(r['has_school_match']),
                'school_name': str(r['school_name'])           if pd.notna(r['school_name'])  else '',
            }
        if pn and pn not in seg_info[oid]['pnames']:
            seg_info[oid]['pnames'].append(pn)

    # Build timing lookup
    timing_lkp = {}
    for _, r in timing.iterrows():
        oid = int(r['object_id'])
        timing_lkp.setdefault(oid, []).append({
            'days':  str(r['days']),
            'cat':   str(r['time_category']),
            'open':  str(r['open_time']),
            'close': str(r['close_time']),
            'notes': str(r['notes']) if pd.notna(r['notes']) else '',
        })

    print("Building data arrays...")
    schools  = build_schools(matched, segments_orig, seg_info)
    excluded = build_excluded(segments_orig)
    segs     = build_segments(segments_treated, seg_info, timing_lkp)

    data = {'schools': schools, 'excluded': excluded, 'segments': segs}
    js   = 'const DASHBOARD_DATA=' + json.dumps(data, separators=(',', ':')) + ';'

    with open(OUTPUT_JS, 'w') as f:
        f.write(js)

    print(f"\n✓ Written: {OUTPUT_JS}")
    print(f"  Schools:  {len(schools)} ({sum(1 for s in schools if s['t']=='case')} case, {sum(1 for s in schools if s['t']=='ctrl')} ctrl)")
    print(f"  Excluded: {len(excluded)}")
    print(f"  Segments: {len(segs)}")
    print(f"  File size: {len(js):,} chars")
    print()
    print("To add years-in-program data:")
    print("  Edit dashboard_data.js and change 'yrs':null to 'yrs':N for each school,")
    print("  OR add a 'years_in_program.csv' column to your matched CSV and re-run this script.")


if __name__ == '__main__':
    main()