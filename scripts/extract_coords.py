#!/usr/bin/env python3
"""Extract station coordinates from merged_2025.json into data/station_coords.json.

Maps "CITY, ST" format from merged_2025.json to "City State" format used in collated.csv.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

STATE_ABBREV = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
    'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
    'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
    'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
    'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
    'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
    'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
    'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
    'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
    'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
    'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia',
}


def main():
    merged_path = ROOT / 'constraint_satisfaction' / 'data' / 'merged_2025.json'
    with open(merged_path) as f:
        merged = json.load(f)

    # Get CSV location names for validation
    csv_path = ROOT / 'data' / 'collated.csv'
    with open(csv_path) as f:
        headers = next(csv.reader(f))
    csv_locs = {h.replace(' (raw)', '') for h in headers if '(raw)' in h}

    coords = {}
    for merged_name, info in merged['locations'].items():
        parts = merged_name.split(', ')
        if len(parts) != 2:
            continue
        city = parts[0].title()
        state_full = STATE_ABBREV.get(parts[1], parts[1])
        csv_name = f'{city} {state_full}'
        if csv_name in csv_locs:
            coords[csv_name] = {'lat': round(info['lat'], 4), 'lon': round(info['lon'], 4)}

    out_path = ROOT / 'data' / 'station_coords.json'
    with open(out_path, 'w') as f:
        json.dump(coords, f, indent=2)

    print(f'Wrote {len(coords)} station coordinates to {out_path}')
    missing = csv_locs - set(coords.keys())
    if missing:
        print(f'CSV locations without coordinates ({len(missing)}): {sorted(missing)}')


if __name__ == '__main__':
    main()
