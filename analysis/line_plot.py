import matplotlib.pyplot as plt
import pandas as pd

from analysis.utils import load_current_forecast_data, smooth_timeseries


def plot_pollen_trends(df, location=None, smooth_method=None, smooth_params=None):
    """Create a line plot of pollen trends by location."""
    plt.figure(figsize=(12, 6))

    if location is not None:
        locations = [location]
    else:
        locations = sorted(df["location"].unique())

    for location in locations:
        location_data = df[df["location"] == location]
        dates = pd.to_datetime(location_data["date"])
        indices = location_data["index"]

        # Plot raw data
        plt.plot(
            dates,
            indices,
            marker="o",
            alpha=0.3,
            label=f"{location} (raw)",
        )

        # Plot smoothed data if method specified
        if smooth_method is not None:
            params = smooth_params or {}  # use empty dict if no params provided
            smoothed = smooth_timeseries(indices, method=smooth_method, **params)
            plt.plot(
                dates,
                smoothed,
                "-",
                label=f"{location} ({smooth_method})",
            )

    print(len(location_data))

    plt.xlabel("Date")
    plt.ylabel("Pollen Index")
    plt.title("Pollen Index Trends by Location")
    plt.xticks(rotation=45)
    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plt.grid(True)


def main():
    data_directory = "s3_data"
    location = "SOUTH SAN FRANCISCO, CA"
    # location = None

    # Select smoothing method and parameters
    # smooth_method = "kalman"  # one of: 'sma', 'savgol', 'lowess', 'kalman'
    # smooth_params = {}  # parameters for the chosen method

    # Example parameter sets for different methods:
    # smooth_method = "savgol"
    # smooth_params = {"window": 5, "polyorder": 2}

    smooth_method = "lowess"
    smooth_params = {"frac": 0.1}

    # smooth_method = 'sma'
    # smooth_params = {'window': 5}

    # Load data
    df = load_current_forecast_data(data_directory)

    # Print some basic statistics
    print("\nData Summary:")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"\nNumber of locations: {df['location'].nunique()}")
    print("\nLocations:", sorted(df["location"].unique()))

    # Create visualization
    plot_pollen_trends(df, location, smooth_method, smooth_params)
    plt.show()

    return df


if __name__ == "__main__":
    df = main()
