import json
import os 
import boto3
import botocore
import pandas as pd

AWS_ACCESS_KEY = os.environ["ACCESS_KEY"]
AWS_SECRET_ACCESS_KEY = os.environ["SECRET_ACCESS_KEY"]
SOURCE_BUCKET_NAME = os.environ["SOURCE_BUCKET_NAME"]

def lambda_handler(event, context):
	
	s3 = boto3.client("s3", aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
	
	try:
		s3.head_object(Bucket=SOURCE_BUCKET_NAME, Key='results.csv')
	except botocore.exceptions.ClientError as e:
		if e.response['Error']['Code'] == "404":
			return { 'message': 'File doesn\'t exist in S3 bucket.'}
		else:
			return { 'message': 'Something went wrong.'}

	response = s3.head_object(Bucket=SOURCE_BUCKET_NAME, Key='results.csv')

	datetime_value = response["LastModified"]

	s3.download_file(SOURCE_BUCKET_NAME, 'results.csv', '/tmp/results.csv')
	results_df = pd.read_csv('/tmp/results.csv', sep = ',', header=0)

	result = results_df.to_json(orient="records")
	
	parsed = json.loads(result)
	parsed.sort(key=lambda x: x["risk_by_sentiment_analysis"], reverse=True)
	parsed = parsed[0:10]

	return {
		"statusCode": 200,
		"body": json.dumps({'date': str(datetime_value.strftime('%d %B %Y')), 'data': parsed}, indent=4),
		'headers': {
			'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
			'Access-Control-Allow-Methods': 'GET,OPTIONS',
			'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json',
        },
	}
