import os

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()


def download_s3_bucket(bucket_name, local_directory):
    """
    Download all files from an S3 bucket to a local directory.

    Args:
        bucket_name (str): Name of the S3 bucket
        local_directory (str): Local directory to save files
    """
    # Create S3 client
    s3_client = boto3.client("s3")

    try:
        # Create local directory if it doesn't exist
        if not os.path.exists(local_directory):
            os.makedirs(local_directory)

        # List all objects in the bucket
        paginator = s3_client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(Bucket=bucket_name)

        # Download each object
        for page in page_iterator:
            if "Contents" in page:
                for obj in page["Contents"]:
                    # Get the file path
                    key = obj["Key"]
                    local_file_path = os.path.join(local_directory, key)

                    # Create directories if the file is in a subdirectory
                    os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

                    # Download the file
                    print(f"Downloading: {key}")
                    s3_client.download_file(bucket_name, key, local_file_path)

        print("Download completed successfully!")

    except ClientError as e:
        print(f"Error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise


# Usage example
if __name__ == "__main__":
    bucket_name = os.getenv("AWS_BUCKET_NAME")
    local_directory = "s3_data"
    download_s3_bucket(bucket_name, local_directory)
