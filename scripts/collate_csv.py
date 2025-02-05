import warnings

import pandas as pd
import pandas.errors

from analysis.utils import load_current_forecast_data, smooth_timeseries

warnings.filterwarnings("ignore", category=pandas.errors.PerformanceWarning)

# State abbreviation to full name mapping
STATE_NAMES = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
    "DC": "District of Columbia",
}


def format_location(loc):
    # Split into city and state
    city, state = loc.split(",")
    state = state.strip()

    # Properly capitalize city (handle multi-word cities)
    city = " ".join(word.capitalize() for word in city.lower().split())

    # Convert state abbreviation to full name
    full_state = STATE_NAMES[state]

    return f"{city} {full_state}"


# Load data
df = load_current_forecast_data("s3_data")

# Create wide format dataframe
dates = sorted(df["date"].unique())
locations = sorted(df["location"].unique())
wide_df = pd.DataFrame({"date": dates})

# Add raw data columns
for loc in locations:
    loc_data = df[df["location"] == loc].set_index("date")["index"]
    formatted_loc = format_location(loc)
    wide_df[f"{formatted_loc} (raw)"] = wide_df["date"].map(loc_data)

# Add smoothed data columns
smooth_method = "lowess"
smooth_params = {"frac": 0.1}

for loc in locations:
    loc_data = df[df["location"] == loc]["index"]
    smoothed = smooth_timeseries(loc_data, method=smooth_method, **smooth_params)
    formatted_loc = format_location(loc)
    wide_df[f"{formatted_loc} (smoothed)"] = smoothed

wide_df = wide_df.iloc[:, :]
wide_df.to_csv("collated.csv", index=False, encoding="utf-8")
