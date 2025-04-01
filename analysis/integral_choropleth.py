import argparse
import os
from collections import defaultdict

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Point

from analysis.utils import (
    create_interpolation_grid,
    get_coordinates_dict,
    interpolate_spatial_values,
    load_data,
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
        "--output_directory",
        type=str,
        default="temp",
        help="Directory in which to produce output",
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
        "--interpolation_method",
        choices=["nn", "linear", "rbf", "cloughtocher"],
        default="nn",
        help="Interpolation method: nn (nearest neighbor), linear, rbf, or cloughtocher",
    )
    parser.add_argument(
        "--format",
        choices=["jpeg", "png"],
        default="png",
        help="output file format",
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


def process_data(pollen_data, coords_dict):
    """Process data file and return summed pollen values for all locations."""
    location_sums = defaultdict(float)
    location_coords = {}

    for _, row in pollen_data.iterrows():
        city_state = row["location"]
        value = row["index"]

        if city_state in coords_dict:
            lat, lon = coords_dict[city_state]
            location_coords[city_state] = (lat, lon)
            location_sums[city_state] += value

    # Convert to list of (lat, lon, sum_value) tuples
    summed_data = []
    for loc, coords in location_coords.items():
        lat, lon = coords
        summed_data.append((lat, lon, location_sums[loc]))

    return summed_data


def create_map(
    summed_data,
    interpolation_method,
    output_directory,
    save_format="jpeg",
    dpi=100,
):
    # Get basic components
    lon_mesh, lat_mesh = create_interpolation_grid()
    url = (
        "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
    )
    world = gpd.read_file(url)
    usa = world[world.NAME == "United States of America"]

    output_size = (900, 375)
    figsize = (output_size[0] / dpi, output_size[1] / dpi)

    # Create figure with specified size
    fig = plt.figure(figsize=figsize, dpi=dpi)
    ax = plt.axes(
        projection=ccrs.LambertConformal(
            central_longitude=-98.5795, central_latitude=39.8283
        )
    )

    # Adjust text sizes based on output size
    title_size = max(8, min(12, output_size[0] / 50))
    plt.rcParams.update({"font.size": max(6, min(10, output_size[0] / 60))})

    # Set up base map features
    ax.add_feature(cfeature.STATES)
    ax.add_feature(cfeature.COASTLINE)
    ax.set_extent([-125, -66.5, 24, 50], ccrs.Geodetic())

    # Extract data
    lats, lons, values = zip(*summed_data)

    # Create interpolated surface
    z_mesh = interpolate_spatial_values(
        lons, lats, values, lon_mesh, lat_mesh, interpolation_method
    )
    z_mesh_masked = create_masked_plot(lon_mesh, lat_mesh, z_mesh, usa.geometry)

    # Create the choropleth
    mesh = ax.pcolormesh(
        lon_mesh,
        lat_mesh,
        z_mesh_masked,
        transform=ccrs.PlateCarree(),
        cmap="RdYlGn_r",
    )
    plt.colorbar(mesh, ax=ax, label="Total Pollen Index", aspect=30, shrink=0.93)

    # Add points for measurement locations
    scatter_size = max(2, min(5, output_size[0] / 200))
    ax.scatter(
        lons,
        lats,
        c="black",
        s=scatter_size,
        transform=ccrs.PlateCarree(),
        alpha=0.5,
    )

    plt.title("Total Pollen Index Over Time", fontsize=title_size)

    # Save the plot
    os.makedirs(output_directory, exist_ok=True)
    output_file = f"{output_directory}/total_pollen_map.{save_format}"
    plt.savefig(
        output_file,
        dpi=dpi,
        bbox_inches="tight",
        pad_inches=0.1,
        format=save_format,
    )
    plt.close()


def main(args):
    coords_dict = get_coordinates_dict()
    pollen_data = load_data(args.data_directory)

    summed_data = process_data(pollen_data, coords_dict)

    create_map(
        summed_data,
        args.interpolation_method,
        args.output_directory,
        args.format,
    )


if __name__ == "__main__":
    args = parse_args()
    main(args)
