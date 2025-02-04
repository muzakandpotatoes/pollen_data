import json
import logging
import os
import sys
from datetime import datetime

lib_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "lib")
sys.path.append(lib_dir)

import boto3
from pollen_data import fetch_all_forecasts, format_jsonl


def lambda_handler(event, context):
    date = datetime.now().strftime("%Y%m%d")
    periods = ["current", "extended", "historic"]

    try:
        for period in periods:
            forecasts = fetch_all_forecasts(period)

            s3 = boto3.client("s3")
            s3.put_object(
                Bucket="pollendatabucket",
                Key=f"{date}_{period}.jsonl",
                Body=format_jsonl(forecasts),
            )

        return {"statusCode": 200, "body": json.dumps("Data stored successfully")}
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return {"statusCode": 500, "body": json.dumps("An error occurred")}
