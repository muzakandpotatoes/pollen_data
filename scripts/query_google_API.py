import os
from pprint import pprint  # For better formatted output

import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
base_url = "https://pollen.googleapis.com/v1/forecast:lookup"

params = {
    "key": api_key,
    "location.latitude": 30.2672,
    "location.longitude": -97.7431,
    "days": 1,
    "plantsDescription": True,
}

response = requests.get(base_url, params=params)

if response.status_code == 200:
    data = response.json()
    pprint(data)  # Let's see the full response structure
else:
    print(f"Error: {response.status_code}")
    print(response.text)
