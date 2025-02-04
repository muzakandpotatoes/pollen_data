import argparse
import json
from datetime import datetime

import jsonlines
import requests

from lambda_src.pollen_data import (
    fetch_all_forecasts,
    fetch_map_data,
    fetch_xml_locations,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fetch pollen data for a specific date."
    )
    parser.add_argument("--sitemap", action="store_true")
    parser.add_argument("--map", action="store_true")
    parser.add_argument("--historic", action="store_true")
    parser.add_argument("--current", action="store_true")
    parser.add_argument("--extended", action="store_true")

    return parser.parse_args()


def main(args):
    date = datetime.now().strftime("%Y%m%d")
    if args.sitemap:
        try:
            data = fetch_xml_locations()
            for datum in data:
                print(datum)
            with open("data/sitemap.json", "w") as f:
                json.dump(data, f)
        except requests.HTTPError as e:
            print(f"HTTP error occurred: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

    if args.map:
        try:
            data = fetch_map_data()
            with open("data/map.json", "w") as f:
                json.dump(data, f)
        except requests.HTTPError as e:
            print(f"HTTP error occurred: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

    if args.current:
        forecasts = fetch_all_forecasts("current")
        with jsonlines.open(f"data/{date}_current.jsonl", mode="w") as f:
            f.write_all(forecasts)

    if args.extended:
        forecasts = fetch_all_forecasts("extended")
        with jsonlines.open(f"data/{date}_extended.jsonl", mode="w") as f:
            f.write_all(forecasts)

    if args.historic:
        forecasts = fetch_all_forecasts("historic")
        with jsonlines.open(f"data/{date}_historic.jsonl", mode="w") as f:
            f.write_all(forecasts)


if __name__ == "__main__":
    args = parse_args()
    main(args)
