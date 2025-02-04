import argparse
from collections import defaultdict

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import geopandas as gpd
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Point

from analysis.utils import (
    create_interpolation_grid,
    get_coordinates_dict,
    interpolate_spatial_values,
    load_current_forecast_data,
    smooth_timeseries,
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data_directory",
        type=str,
        default="s3_data",
        help="Directory with current pollen forecasts over the date range",
    )
    parser.add_argument(
        "--start_date",
        type=str,
        default=None,
        help="Start date in YYYY-MM-DD format (default: earliest available)",
    )
    parser.add_argument(
        "--end_date",
        type=str,
        default=None,
        help="End date in YYYY-MM-DD format (default: latest available)",
    )
    parser.add_argument(
        "--smooth_method",
        choices=["sma", "savgol", "lowess", "kalman"],
        default=None,
        help="Smoothing method to use: sma, savgol, lowess, or kalman",
    )
    parser.add_argument(
        "--interpolation_method",
        choices=["nn", "linear", "rbf", "cloughtocher"],
        default="nn",
        help="Interpolation method: nn (nearest neighbor), linear, rbf, or cloughtocher",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=20,
        help="Frames per second for output animation (default: 20)",
    )

    return parser.parse_args()


def create_masked_plot(lon_mesh, lat_mesh, z_mesh, usa_geom):
    """Create and return masked plot data."""
    mask = np.zeros_like(z_mesh)
    for i in range(lon_mesh.shape[0]):
        for j in range(lon_mesh.shape[1]):
            point = Point(lon_mesh[i, j], lat_mesh[i, j])
            if usa_geom.contains(point).any():
                mask[i, j] = 1
            else:
                mask[i, j] = np.nan

    return z_mesh * mask


def smooth_pollen_data(pollen_df, smooth_method):
    # Create a copy of the input DataFrame to avoid modifying the original
    result_df = pollen_df.copy()

    # Initialize new column for smoothed values
    result_df["smoothed_index"] = float("nan")

    # Get unique locations
    locations = pollen_df["location"].unique()

    # Process each location separately
    for loc in locations:
        # Get data for this location
        loc_data = pollen_df[pollen_df["location"] == loc]

        # Get the smoothed values for this location's time series
        smoothed_values = smooth_timeseries(loc_data["index"], smooth_method)

        # Update the smoothed values in the result DataFrame at the correct indices
        result_df.loc[loc_data.index, "smoothed_index"] = smoothed_values
    result_df["index"] = result_df["smoothed_index"]

    return result_df


def process_data(pollen_data, coords_dict):
    """Process data file and return a dict of date -> pollen values for all locations."""
    date_data = defaultdict(list)

    for _, row in pollen_data.iterrows():
        city_state = row["location"]
        value = row["index"]

        if city_state in coords_dict:
            lat, lon = coords_dict[city_state]

            date_data[row["date"]].append((lat, lon, value))

    return date_data


def create_animation(date_data, interpolation_method, fps):
    """Create animation from data file."""
    # Set up basic components
    lon_mesh, lat_mesh = create_interpolation_grid()

    # first_n_keys = list(date_data.keys())[:1]  # limit for testing purposes
    # date_data = {k: date_data[k] for k in first_n_keys}

    # Get US geometry for masking
    url = (
        "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
    )
    world = gpd.read_file(url)
    usa = world[world.NAME == "United States of America"]

    # Create figure
    fig = plt.figure(figsize=(15, 10))
    ax = plt.axes(
        projection=ccrs.LambertConformal(
            central_longitude=-98.5795, central_latitude=39.8283
        )
    )

    # Set up base map features
    ax.add_feature(cfeature.STATES)
    ax.add_feature(cfeature.COASTLINE)
    ax.set_extent([-125, -66.5, 24, 50], ccrs.Geodetic())

    # Create initial mesh for colorbar
    mesh = ax.pcolormesh(
        lon_mesh,
        lat_mesh,
        np.zeros_like(lon_mesh),
        transform=ccrs.PlateCarree(),
        cmap="RdYlGn_r",
        vmin=0,
        vmax=10,
    )
    plt.colorbar(mesh, ax=ax, label="Pollen Index")

    def update(frame_number):
        ax.clear()
        ax.add_feature(cfeature.STATES)
        ax.add_feature(cfeature.COASTLINE)
        ax.set_extent([-125, -66.5, 24, 50], ccrs.Geodetic())

        date = sorted(date_data.keys())[frame_number]
        frame_data = date_data[date]

        # Unzip the (lat, lon, value) tuples
        lats, lons, values = zip(*frame_data)

        # Create interpolated surface
        z_mesh = interpolate_spatial_values(
            lons, lats, values, lon_mesh, lat_mesh, interpolation_method
        )

        # Mask the data
        z_mesh_masked = create_masked_plot(lon_mesh, lat_mesh, z_mesh, usa.geometry)

        # Plot the data
        mesh = ax.pcolormesh(
            lon_mesh,
            lat_mesh,
            z_mesh_masked,
            transform=ccrs.PlateCarree(),
            cmap="RdYlGn_r",
            vmin=0,
            vmax=10,
        )

        ax.scatter(lons, lats, c="black", s=10, transform=ccrs.PlateCarree(), alpha=0.5)

        plt.title(f"Pollen Index - {date}")
        return (mesh,)

    # Create animation
    anim = animation.FuncAnimation(
        fig,
        update,
        frames=len(date_data),
        interval=500,  # doesn't affect gif output
        blit=False,
    )

    # Save animation
    start_date = min(date_data.keys()) if not args.start_date else args.start_date
    end_date = max(date_data.keys()) if not args.end_date else args.end_date
    smooth_method = "" if not args.smooth_method else args.smooth_method

    anim.save(
        f"pollen_animation_{start_date}_{end_date}_{smooth_method}_{interpolation_method}_{fps}hz.gif",
        writer="pillow",
        fps=fps,
    )
    plt.close()


def main(args):
    args.start_date
    args.end_date

    coords_dict = get_coordinates_dict()
    pollen_data = load_current_forecast_data(args.data_directory)
    if args.smooth_method is not None:
        pollen_data = smooth_pollen_data(pollen_data, args.smooth_method)
    date_data = process_data(
        pollen_data,
        coords_dict,
    )

    create_animation(date_data, args.interpolation_method, args.fps)


if __name__ == "__main__":
    args = parse_args()
    main(args)
