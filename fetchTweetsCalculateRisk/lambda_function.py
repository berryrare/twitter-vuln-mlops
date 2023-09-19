import pandas as pd
import boto3
import botocore
import os
from TwitterRetriever import TwitterRetriever
from RiskAssessor import RiskAssessor

ACCESS_KEY = os.environ["ACCESS_KEY"]
SECRET_ACCESS_KEY = os.environ["SECRET_ACCESS_KEY"]
SOURCE_BUCKET_NAME = os.environ["SOURCE_BUCKET_NAME"]
DEST_BUCKET_NAME = os.environ["DEST_BUCKET_NAME"]
BEARER_TOKEN = os.environ["BEARER_TOKEN"]

def lambda_handler(event, context):

    s3 = boto3.client("s3", aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_ACCESS_KEY)

    tweets_exist = True
    #check if the file exists
    try:
        s3.head_object(Bucket=SOURCE_BUCKET_NAME, Key='tweets.csv')
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            tweets_exist = False
        else:
            return { 'message': 'Something went wrong.'}

    try:
        s3.head_object(Bucket=SOURCE_BUCKET_NAME, Key='vendors_keywords.xlsx')
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            return { 'message': 'vendors_keywords.xlsx doesn\'t exist in S3 bucket.'}
        else:
            return { 'message': 'Something went wrong.'}

    if tweets_exist:
        s3.download_file(SOURCE_BUCKET_NAME, 'tweets.csv', '/tmp/tweets.csv')
        
    s3.download_file(SOURCE_BUCKET_NAME, 'vendors_keywords.xlsx', '/tmp/vendors_keywords.xlsx')

    vendors = pd.read_excel("/tmp/vendors_keywords.xlsx", sheet_name="Vendors").vendorProject.unique()
    keywords = pd.read_excel("/tmp/vendors_keywords.xlsx", sheet_name="Security Phrases", header=None)[0].values

    twitter_retriever = TwitterRetriever(premium = False) 
    risk_assessor = RiskAssessor(twitter_retriever, vendors, keywords, latest = True)

    response = s3.upload_file('/tmp/tweets.csv', SOURCE_BUCKET_NAME, 'tweets.csv')

    risk_df = pd.DataFrame(columns = ["vendor", "relative_risk", "relative_risk_with_popularity",
                                  "absolute_risk", "absolute_risk_with_popularity",
                                  "relative_risk_rank", "risk_by_sentiment_analysis"])

    for vendor in risk_assessor.tweets.vendor.unique():
        relative_risk = risk_assessor.get_relative_vendor_risk(vendor)
        relative_risk_with_popularity = risk_assessor.get_relative_vendor_risk(vendor, True)
        absolute_risk = risk_assessor.get_absolute_vendor_risk(vendor)
        absolute_risk_with_popularity = risk_assessor.get_absolute_vendor_risk(vendor, True)
        relative_risk_rank = risk_assessor.get_relative_vendor_risk_rank(vendor)
        risk_by_sentiment_analysis = risk_assessor.get_vendor_risk_by_sentiment_analysis(vendor)
        risk_df.loc[len(risk_df)] = [vendor, relative_risk, relative_risk_with_popularity, 
                                     absolute_risk, absolute_risk_with_popularity, 
                                     relative_risk_rank, risk_by_sentiment_analysis]


    risk_df.to_csv('/tmp/results.csv', index = False)
    response = s3.upload_file('/tmp/results.csv', DEST_BUCKET_NAME, 'results.csv')

    return {
        "statusCode": 200,
        "body": "Success",
    }
