
`data/map.json` contains the results of a call to pollen.com's `map` API. It's assumed that the location fields for the return value from this API call represent all members of the partition of the US into pollen-forecast regions. I'm unsure whether this assumption is correct.

`data/map_augmented.json` additionally includes ZIP code information for each location in `map.json`, and removes locations outside the contiguous 48 US states, which seem not to be tracked by pollen.com.

Pollen.com provides APIs for historic (previous 30 d) data, current day, and 5 day forecast. Current day counts are accompanied by top pollen sources.

Pollen.com also provides expected pollen counts of each type (tree, grass, ragweed) for each location for each week of the year, but I have found this to be unreliable, hence this project.

--

Notes on setting up the AWS Lambda function to fetch daily:

- log into the right account / user
- make a IAM role with AWSLambdaExecute permission policy
- locally, make a script:
	- `lambda_function.py` with function `def lambda_handler(event, context)`
	- install dependencies in `src` with script `pip install -t src/lib -r requirements.txt` 
	- see `lambda_function.py` for how to load dependencies fom `lib`
	- zip script up `zip -r ../[package_name].zip .`
- make a lambda function
- give lambda function appropriate role during setup or in Configurations -> Permissions
- upload zipped package in Code -> Code source
- test with Test -> Test event
- add an EventBridge trigger

## Downloading data stored on S3
Get AWS creds:
1. Log into the AWS web console
2. Go to IAM > Security Credentials, and create access key
3. Copy the access keys into `.env`

Run
```
source .venv/bin/activate
python -m scripts.download_s3_data
```

Delete the security credentials.

## Update all artifacts

Download data from S3 as above, then run
```

python -m scripts.collate_csv
echo "CSV collation completed"
python -m analysis.choropleth --smooth_method=lowess
echo "Choropleth with lowess smoothing completed"
python -m analysis.choropleth
echo "Standard choropleth analysis completed"
python -m analysis.integral_choropleth
echo "Integral choropleth analysis completed"
```
This updates the csv file used to inform the interactive chart, and makes updated animations. Animations can take a while to render.en

