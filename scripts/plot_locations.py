import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt

from analysis.utils import get_coordinates_dict


def plot_locations():
    # Get coordinates dictionary
    coords = get_coordinates_dict()

    # Create figure and axis with projection
    fig = plt.figure(figsize=(24, 16))
    ax = plt.axes(
        projection=ccrs.LambertConformal(
            central_longitude=-98.5795, central_latitude=39.8283
        )
    )

    # Add map features
    ax.add_feature(cfeature.STATES)
    ax.add_feature(cfeature.COASTLINE)

    # Set extent to cover continental US with some padding
    ax.set_extent([-125, -66.5, 24, 50], ccrs.Geodetic())

    # Plot each location
    for city, (lat, lon) in coords.items():
        # Plot point
        ax.plot(lon, lat, "ro", transform=ccrs.Geodetic(), markersize=3)

        # Add city label with slight offset
        ax.text(
            lon + 0.3,
            lat + 0.3,
            city,
            transform=ccrs.Geodetic(),
            fontsize=6,
            bbox=dict(facecolor="white", alpha=0.7, edgecolor="none"),
        )

    plt.title("US Weather Station Locations", fontsize=16, pad=20)

    # Add gridlines
    ax.gridlines(draw_labels=True)

    plt.show()

    return fig, ax


if __name__ == "__main__":
    fig, ax = plot_locations()
