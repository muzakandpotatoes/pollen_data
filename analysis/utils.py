import glob
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from filterpy.kalman import KalmanFilter
from scipy.interpolate import (
    CloughTocher2DInterpolator,
    LinearNDInterpolator,
    NearestNDInterpolator,
    Rbf,
)
from scipy.signal import savgol_filter
from statsmodels.nonparametric.smoothers_lowess import lowess

### DATA MUNGING


def read_historic_data_file(file_path):
    """Read a single JSONL file and extract historical pollen data."""
    data = []

    with open(file_path, "r") as f:
        for line in f:
            record = json.loads(line)
            location = record["Location"]
            forecast_date = record["ForecastDate"].split("T")[0]  # Extract date part

            # Process all periods in the location data
            for period in location["periods"]:
                period_date = period["Period"].split("T")[0]  # Extract date part

                data.append(
                    {
                        "date": period_date,
                        "location": f"{location['City']}, {location['State']}",
                        "index": period["Index"],
                    }
                )
    return data


def read_current_forecast_file(file_path):
    """Read a single JSONL file and extract today's pollen data."""
    data = []
    date_str = Path(file_path).stem.split("_")[0]
    file_date = datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d")

    with open(file_path, "r") as f:
        for line in f:
            record = json.loads(line)
            location = record["Location"]

            # Find the "Today" period
            today_data = next(
                (p for p in location["periods"] if p["Type"] == "Today"), None
            )

            if today_data:
                data.append(
                    {
                        "date": file_date,
                        "location": f"{location['City']}, {location['State']}",
                        "index": today_data["Index"],
                    }
                )
    return data


def load_current_forecast_data(data_dir="s3_data"):
    """Load and combine data from all JSONL files."""
    files = sorted(glob.glob(f"{data_dir}/*_current.jsonl"))
    all_data = []

    for file_path in files:
        file_data = read_current_forecast_file(file_path)
        all_data.extend(file_data)

    return pd.DataFrame(all_data)


def load_data(data_dir="s3_data"):
    """Load data including the earliest available records"""
    file_path = sorted(glob.glob(f"{data_dir}/*_historic.jsonl"))[0]
    early_data = pd.DataFrame(read_historic_data_file(file_path))
    data = load_current_forecast_data(data_dir)

    data = pd.concat([early_data, data], axis=0)
    data = data.drop_duplicates(subset=["date", "location"], keep="first")

    return pd.DataFrame(data)


### TIMESERIES SMOOTHING


def setup_kalman():
    """Initialize Kalman filter for pollen data smoothing."""
    kf = KalmanFilter(dim_x=2, dim_z=1)  # state: [position, velocity]
    dt = 1.0  # 1 day between measurements

    kf.F = np.array([[1.0, dt], [0.0, 1.0]])
    kf.H = np.array([[1.0, 0.0]])
    kf.R = 5
    kf.Q = np.array([[0.1, 0.0], [0.0, 0.1]])

    return kf


def smooth_kalman(data):
    """Apply Kalman filter smoothing to time series."""
    kf = setup_kalman()
    kf.x = np.array([[data.iloc[0]], [0.0]])
    kf.P *= 100

    smoothed = []
    for measurement in data:
        kf.predict()
        kf.update(measurement)
        smoothed.append(kf.x[0, 0])

    return np.array(smoothed)


def smooth_timeseries(data, method="lowess", **kwargs):
    """Smooth time series data using specified method.

    Args:
        data: pandas Series of values to smooth
        method: one of ['sma', 'savgol', 'lowess', 'kalman']
        kwargs: additional parameters for specific smoothing methods
    """
    if method == "sma":
        window = kwargs.get("window", 5)
        return data.rolling(window=window, center=True).mean()

    elif method == "savgol":
        window = kwargs.get("window", 5)
        polyorder = kwargs.get("polyorder", 2)
        return savgol_filter(data, window_length=window, polyorder=polyorder)

    elif method == "lowess":
        frac = kwargs.get("frac", 0.1)
        return lowess(data, np.arange(len(data)), frac=frac)[:, 1]

    elif method == "kalman":
        return smooth_kalman(data)

    else:
        raise ValueError(f"Unknown smoothing method: {method}")


### MAP MUNGING


def get_coordinates_dict():
    """Dictionary of coordinates for all locations."""
    return {
        "ABERDEEN, SD": (45.4647, -98.4864),
        "ABILENE, TX": (32.4487, -99.7331),
        "ALAMOSA, CO": (37.4695, -105.8700),
        "ALBANY, GA": (31.5785, -84.1557),
        "ALBANY, NY": (42.6526, -73.7562),
        "ALBUQUERQUE, NM": (35.0844, -106.6504),
        "ALLENTOWN, PA": (40.6023, -75.4714),
        "ALPENA, MI": (45.0617, -83.4327),
        "ALTOONA, PA": (40.5187, -78.3947),
        "AMARILLO, TX": (35.2220, -101.8313),
        "ASHEVILLE, NC": (35.5951, -82.5516),
        "ASTORIA, OR": (46.1879, -123.8313),
        "ATHENS, GA": (33.9519, -83.3576),
        "ATLANTA, GA": (33.7490, -84.3880),
        "ATLANTIC CITY, NJ": (39.3643, -74.4229),
        "AUGUSTA, GA": (33.4735, -82.0107),
        "AUSTIN, TX": (30.2672, -97.7431),
        "BAKERSFIELD, CA": (35.3733, -119.0187),
        "BALTIMORE, MD": (39.2904, -76.6122),
        "BANGOR, ME": (44.8016, -68.7712),
        "BATON ROUGE, LA": (30.4515, -91.1871),
        "BEAUFORT, SC": (32.4316, -80.6698),
        "BEAUMONT, TX": (30.0802, -94.1266),
        "BECKLEY, WV": (37.7782, -81.1882),
        "BEMIDJI, MN": (47.4716, -94.8827),
        "BELLINGHAM, WA": (48.7519, -122.4787),
        "BILLINGS, MT": (45.7833, -108.5007),
        "BINGHAMTON, NY": (42.0987, -75.9180),
        "BIRMINGHAM, AL": (33.5207, -86.8025),
        "BISMARCK, ND": (46.8083, -100.7837),
        "BOISE, ID": (43.6150, -116.2023),
        "BOSTON, MA": (42.3601, -71.0589),
        "BOWLING GREEN, KY": (36.9685, -86.4808),
        "BRIDGEPORT, CT": (41.1792, -73.1894),
        "BRISTOL, TN": (36.5951, -82.1887),
        "BROWNSVILLE, TX": (25.9018, -97.4975),
        "BUFFALO, NY": (42.8864, -78.8784),
        "BURLINGTON, IA": (40.8075, -91.1127),
        "BURLINGTON, VT": (44.4759, -73.2121),
        "BURNS, OR": (43.5863, -119.0546),
        "CAPE GIRARDEAU, MO": (37.3059, -89.5181),
        "CARIBOU, ME": (46.8653, -67.9986),
        "CASPER, WY": (42.8501, -106.3252),
        "CEDAR CITY, UT": (37.6775, -113.0619),
        "CEDAR RAPIDS, IA": (41.9779, -91.6656),
        "CHAMPAIGN, IL": (40.1164, -88.2434),
        "CHARLESTON, SC": (32.7765, -79.9311),
        "CHARLESTON, WV": (38.3498, -81.6326),
        "CHARLOTTE, NC": (35.2271, -80.8431),
        "CHATTANOOGA, TN": (35.0456, -85.3097),
        "CHEYENNE, WY": (41.1400, -104.8202),
        "CHICAGO, IL": (41.8781, -87.6298),
        "CINCINNATI, OH": (39.1031, -84.5120),
        "CLEVELAND, OH": (41.4993, -81.6944),
        "COLORADO SPRINGS, CO": (38.8339, -104.8214),
        "COLUMBIA, MO": (38.9517, -92.3341),
        "COLUMBUS, GA": (32.4610, -84.9877),
        "COLUMBUS, OH": (39.9612, -82.9988),
        "CONCORD, NH": (43.2081, -71.5376),
        "CONCORDIA, KS": (39.5700, -97.6625),
        "CORPUS CHRISTI, TX": (27.8006, -97.3964),
        "DAYTON, OH": (39.7589, -84.1916),
        "DAYTONA BEACH, FL": (29.2108, -81.0228),
        "DEL RIO, TX": (29.3627, -100.8968),
        "DENVER, CO": (39.7392, -104.9903),
        "DETROIT, MI": (42.3314, -83.0458),
        "DICKINSON, ND": (46.8792, -102.7896),
        "DODGE CITY, KS": (37.7528, -100.0171),
        "DOVER, DE": (39.1582, -75.5244),
        "DUBUQUE, IA": (42.5006, -90.6645),
        "DULUTH, MN": (46.7867, -92.1005),
        "EAU CLAIRE, WI": (44.8114, -91.4984),
        "EAST LANSING, MI": (42.7368, -84.4837),
        "EAST MOLINE, IL": (41.5067, -90.4446),
        "EAST PITTSBURGH, PA": (40.3926, -79.8331),
        "EAST ROCHESTER, NY": (43.1131, -77.4855),
        "EAST SYRACUSE, NY": (43.0645, -76.0711),
        "EL PASO, TX": (31.7619, -106.4850),
        "ELKINS, WV": (38.9237, -79.8467),
        "ELY, NV": (39.2533, -114.8742),
        "ERIE, PA": (42.1292, -80.0851),
        "EUGENE, OR": (44.0521, -123.0868),
        "EUREKA, CA": (40.8021, -124.1637),
        "EVANSVILLE, IN": (37.9716, -87.5711),
        "FARMINGTON, NM": (36.7281, -108.2087),
        "FLAGSTAFF, AZ": (35.1983, -111.6513),
        "FLINT, MI": (43.0125, -83.6875),
        "FLORENCE, SC": (34.1954, -79.7626),
        "FORT DRUM, NY": (44.0509, -75.7207),
        "FORT SMITH, AR": (35.3859, -94.3985),
        "FORT WAYNE, IN": (41.0793, -85.1394),
        "FORT WORTH, TX": (32.7555, -97.3308),
        "FRESNO, CA": (36.7378, -119.7871),
        "GLASGOW, MT": (48.1973, -106.6354),
        "GOODLAND, KS": (39.3486, -101.7107),
        "GRAND FORKS, ND": (47.9253, -97.0329),
        "GRAND ISLAND, NE": (40.9264, -98.3420),
        "GRAND JUNCTION, CO": (39.0639, -108.5506),
        "GRAND RAPIDS, MI": (42.9634, -85.6681),
        "GREAT FALLS, MT": (47.5065, -111.3009),
        "GREEN BAY, WI": (44.5133, -88.0133),
        "GREENSBORO, NC": (36.0726, -79.7920),
        "GREENVILLE, SC": (34.8526, -82.3940),
        "GULFPORT, MS": (30.3674, -89.0928),
        "HATTERAS, NC": (35.2146, -75.6900),
        "HEART BUTTE, MT": (48.2883, -112.8407),
        "HOUGHTON LAKE, MI": (44.3145, -84.7654),
        "HOUSTON, TX": (29.7604, -95.3698),
        "HUNTINGTON, WV": (38.4192, -82.4452),
        "HUNTSVILLE, AL": (34.7304, -86.5861),
        "HURON, SD": (44.3633, -98.2148),
        "INDIANAPOLIS, IN": (39.7684, -86.1581),
        "INTERNATIONAL FALLS, MN": (48.6023, -93.4040),
        "JACKSON, KY": (37.5533, -83.3835),
        "JACKSON, MS": (32.2988, -90.1848),
        "JACKSON, TN": (35.6145, -88.8139),
        "JACKSONVILLE, FL": (30.3322, -81.6557),
        "JAMESTOWN, ND": (46.9106, -98.7084),
        "JAMESTOWN, NY": (42.0970, -79.2353),
        "KALISPELL, MT": (48.1920, -114.3168),
        "KANSAS CITY, MO": (39.0997, -94.5786),
        "KEY WEST, FL": (24.5551, -81.7800),
        "KNOXVILLE, TN": (35.9606, -83.9207),
        "LAKE CHARLES, LA": (30.2266, -93.2174),
        "LAKE DALLAS, TX": (33.1290, -97.0250),
        "LANDER, WY": (42.8333, -108.7307),
        "LAREDO, TX": (27.5054, -99.5075),
        "LEWISTON, ID": (46.4166, -117.0177),
        "LEXINGTON, KY": (38.0406, -84.5037),
        "LINCOLN, NE": (40.8136, -96.7026),
        "LITTLE ROCK, AR": (34.7465, -92.2896),
        "LOS ANGELES, CA": (34.0522, -118.2437),
        "LOUISVILLE, KY": (38.2527, -85.7585),
        "LUBBOCK, TX": (33.5779, -101.8552),
        "LYNCHBURG, VA": (37.4138, -79.1422),
        "MACON, GA": (32.8407, -83.6324),
        "MADISON, WI": (43.0731, -89.4012),
        "MEDFORD, OR": (42.3265, -122.8756),
        "MEMPHIS, TN": (35.1495, -90.0490),
        "MERIDIAN, MS": (32.3643, -88.7037),
        "MIAMI, FL": (25.7617, -80.1918),
        "MIDDLETOWN, PA": (40.1992, -76.7321),
        "MIDLAND, TX": (31.9973, -102.0779),
        "MILES CITY, MT": (46.4083, -105.8406),
        "MINOT, ND": (48.2327, -101.2926),
        "MISSOULA, MT": (46.8721, -113.9940),
        "MOBILE, AL": (30.6954, -88.0399),
        "MONROE, LA": (32.5093, -92.1193),
        "MONTGOMERY, AL": (32.3792, -86.3077),
        "MONTPELIER, VT": (44.2601, -72.5754),
        "MUSKEGON, MI": (43.2342, -86.2484),
        "NASHVILLE, TN": (36.1627, -86.7816),
        "NEW HARTFORD, CT": (41.8812, -72.9776),
        "NEW ORLEANS, LA": (29.9511, -90.0715),
        "NEW PHILADELPHIA, OH": (40.4898, -81.4457),
        "NEW YORK, NY": (40.7128, -74.0060),
        "NEWARK, NJ": (40.7357, -74.1724),
        "NORFOLK, NE": (42.0285, -97.4172),
        "NORFOLK, VA": (36.8508, -76.2859),
        "NORTH CANTON, OH": (40.8759, -81.4023),
        "NORTH LAS VEGAS, NV": (36.1989, -115.1175),
        "NORTH PLATTE, NE": (41.1403, -100.7601),
        "OKLAHOMA CITY, OK": (35.4676, -97.5164),
        "OLYMPIA, WA": (47.0379, -122.9007),
        "OMAHA, NE": (41.2565, -95.9345),
        "ORLANDO, FL": (28.5383, -81.3792),
        "PENDLETON, OR": (45.6721, -118.7886),
        "PENSACOLA, FL": (30.4213, -87.2169),
        "PEORIA, IL": (40.6936, -89.5890),
        "PHOENIX, AZ": (33.4484, -112.0740),
        "PIERRE, SD": (44.3683, -100.3510),
        "PLYMOUTH, MN": (45.0105, -93.4555),
        "POCATELLO, ID": (42.8713, -112.4455),
        "PORTLAND, ME": (43.6591, -70.2568),
        "PORTLAND, OR": (45.5155, -122.6789),
        "PRESCOTT, AZ": (34.5400, -112.4685),
        "PRICE, UT": (39.5994, -110.8107),
        "PROVIDENCE, RI": (41.8240, -71.4128),
        "PUEBLO, CO": (38.2544, -104.6091),
        "QUINCY, IL": (39.9356, -91.4098),
        "RALEIGH, NC": (35.7796, -78.6382),
        "RAPID CITY, SD": (44.0805, -103.2310),
        "REDDING, CA": (40.5865, -122.3917),
        "RENO, NV": (39.5296, -119.8138),
        "RICHMOND, VA": (37.5407, -77.4360),
        "ROANOKE, VA": (37.2710, -79.9414),
        "ROCHESTER, MN": (44.0121, -92.4802),
        "ROCKFORD, IL": (42.2711, -89.0937),
        "ROSWELL, NM": (33.3943, -104.5230),
        "SACRAMENTO, CA": (38.5816, -121.4944),
        "SALEM, OR": (44.9429, -123.0351),
        "SALT LAKE CITY, UT": (40.7608, -111.8910),
        "SAN ANGELO, TX": (31.4638, -100.4370),
        "SAN ANTONIO, TX": (29.4241, -98.4936),
        "SAN DIEGO, CA": (32.7157, -117.1611),
        "SANTA BARBARA, CA": (34.4208, -119.6982),
        "SANTA FE, NM": (35.6870, -105.9378),
        "SAVANNAH, GA": (32.0809, -81.0912),
        "SCOTTSBLUFF, NE": (41.8666, -103.6672),
        "SCRANTON, PA": (41.4090, -75.6624),
        "SEATTLE, WA": (47.6062, -122.3321),
        "SHERIDAN, WY": (44.7972, -106.9562),
        "SHREVEPORT, LA": (32.5252, -93.7502),
        "SILVER CITY, NM": (32.7701, -108.2803),
        "SIOUX CITY, IA": (42.4963, -96.4049),
        "SIOUX FALLS, SD": (43.5460, -96.7313),
        "SOUTH BEND, IN": (41.6764, -86.2520),
        "SOUTH MILWAUKEE, WI": (42.9103, -87.8602),
        "SOUTH SAN FRANCISCO, CA": (37.6547, -122.4077),
        "SPOKANE, WA": (47.6587, -117.4260),
        "SPRINGFIELD, IL": (39.7817, -89.6501),
        "SPRINGFIELD, MO": (37.2090, -93.2923),
        "SAINT CLOUD, MN": (45.5579, -94.1632),
        "SAINT LOUIS, MO": (38.6270, -90.1994),
        "STERLING, VA": (39.0062, -77.4286),
        "TALLAHASSEE, FL": (30.4383, -84.2807),
        "TAMPA, FL": (27.9506, -82.4572),
        "TOLEDO, OH": (41.6528, -83.5379),
        "TOPEKA, KS": (39.0473, -95.6752),
        "TRAVERSE CITY, MI": (44.7631, -85.6206),
        "TUCSON, AZ": (32.2226, -110.9747),
        "TULSA, OK": (36.1540, -95.9928),
        "TUPELO, MS": (34.2576, -88.7034),
        "VALENTINE, NE": (42.8725, -100.5507),
        "VICTORIA, TX": (28.8053, -97.0036),
        "WACO, TX": (31.5493, -97.1467),
        "WASHINGTON, DC": (38.8977, -77.0365),
        "WATERLOO, IA": (42.4993, -92.3380),
        "WAUSAUKEE, WI": (45.3791, -87.9587),
        "WEST COLUMBIA, SC": (33.9932, -81.0739),
        "WEST DES MOINES, IA": (41.5772, -93.7119),
        "WEST FARGO, ND": (46.8769, -96.8999),
        "WEST MANSFIELD, OH": (40.4031, -83.5465),
        "WEST PALM BEACH, FL": (26.7153, -80.0534),
        "WICHITA, KS": (37.6872, -97.3301),
        "WICHITA FALLS, TX": (33.9137, -98.4934),
        "WILLIAMSPORT, PA": (41.2414, -77.0011),
        "WILLISTON, ND": (48.1470, -103.6180),
        "WILMINGTON, DE": (39.7447, -75.5466),
        "WILMINGTON, NC": (34.2104, -77.8868),
        "WINNEMUCCA, NV": (40.9730, -117.7357),
        "WORCESTER, MA": (42.2626, -71.8023),
        "YAKIMA, WA": (46.6021, -120.5059),
        "YOUNGSTOWN, OH": (41.0998, -80.6495),
        "YUMA, AZ": (32.6927, -114.6277),
    }


### SPATIAL INTERPOLATION


def create_interpolation_grid():
    """Create a regular grid covering the continental US."""
    # Define grid bounds (continental US)
    lon_min, lon_max = -125, -66.5
    lat_min, lat_max = 24, 50

    # Create grid with 0.5 degree resolution
    grid_resolution = 0.15
    lon_grid = np.arange(lon_min, lon_max, grid_resolution)
    lat_grid = np.arange(lat_min, lat_max, grid_resolution)

    # Create meshgrid for interpolation
    lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)

    return lon_mesh, lat_mesh


def interpolate_spatial_values(
    points_lon, points_lat, values, lon_mesh, lat_mesh, method
):
    """Interpolate pollen values across the grid using RBF."""
    if method == "nn":
        interpolator = NearestNDInterpolator(list(zip(points_lon, points_lat)), values)
    elif method == "linear":
        LinearNDInterpolator(list(zip(points_lon, points_lat)), values)
    elif method == "rbf":
        interpolator = Rbf(
            points_lon, points_lat, values, function="multiquadric", smooth=0.3
        )
    elif method == "cloughtocher":
        interpolator = CloughTocher2DInterpolator(
            list(zip(points_lon, points_lat)), values
        )

    # Interpolate values on the grid
    z_mesh = interpolator(lon_mesh, lat_mesh)

    # Clip negative values to 0 (RBF can produce negative values)
    z_mesh = np.clip(z_mesh, 0, None)

    return z_mesh
