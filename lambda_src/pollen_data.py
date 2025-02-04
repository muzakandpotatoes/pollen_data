import json
import os
import sys
import xml.etree.ElementTree as ET

lib_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "lib")
sys.path.append(lib_dir)

import requests

HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Cookie": "ASP.NET_SessionId=pekta1u1vx213zkm2hnv4qjj; geo=94117; __RequestVerificationToken=S8N_VOJfHHm0z9xNDFH9YdWNtVq5d3FEf7XeojO6dF7kERzcTjaQRSQx5t9Y_wWIcw9kbuV_uM3HDrcngdLkxeh0Rc9PJNTV-cANF7EiKmE1; search=94601",
    "Referer": "https://www.pollen.com/map/",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
}


def fetch_xml_locations():
    url = "https://www.pollen.com/sitemap.xml"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    root = ET.fromstring(response.content)
    locations = [
        elem.text
        for elem in root.findall(
            ".//{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
        )
    ]
    locations.sort()

    return locations


def fetch_forecast(period, zip):
    """period in {historic, current, extended}"""
    url = f"https://www.pollen.com/api/forecast/{period}/pollen/{zip}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()  # Raises an HTTPError for bad responses
    return response.json()


def fetch_all_forecasts(period):
    map_path = os.path.join(os.path.dirname(__file__), "map_augmented.json")
    with open(map_path, "r") as f:
        map_data = json.load(f)

    forecasts = []
    for loc in map_data["Locations"]:
        zip = map_data["Locations"][loc]["ZIP"]
        forecasts.append(fetch_forecast(period, zip))

    return forecasts


def fetch_map_data():
    url = "https://www.pollen.com/api/map"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()  # Raises an HTTPError for bad responses
    return response.json()


def format_jsonl(dict_list):
    return "\n".join(json.dumps(dict) for dict in dict_list)
