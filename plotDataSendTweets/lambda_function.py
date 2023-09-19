import json
import os 
import boto3
import botocore
import datetime
import tweepy
import pandas as pd
import plotly.graph_objects as go

ACCESS_KEY = os.environ["ACCESS_KEY"]
SECRET_ACCESS_KEY = os.environ["SECRET_ACCESS_KEY"]
SOURCE_BUCKET_NAME = os.environ["SOURCE_BUCKET_NAME"]
TW_ACCESS_KEY = os.environ["TW_API_KEY"]
TW_SECRET_ACCESS_KEY = os.environ["TW_API_KEY_SECRET"]
TW_ACCESS_TOKEN = os.environ["TW_ACCESS_TOKEN"]
TW_ACCESS_TOKEN_SECRET = os.environ["TW_ACCESS_TOKEN_SECRET"]

IMAGE_FILENAME = '/tmp/resultsGraph.png'
DEFAULT_TWEET_TEXT = 'Check out this daily snapshot that uses machine learning analysis of recent tweets to assess the security risk of top software vendors.'

def get_auth():
    twitter_keys = {
        'consumer_key': TW_ACCESS_KEY,
        'consumer_secret': TW_SECRET_ACCESS_KEY,
        'access_token_key': TW_ACCESS_TOKEN,
        'access_token_secret': TW_ACCESS_TOKEN_SECRET,
        }
    auth = tweepy.OAuthHandler(twitter_keys['consumer_key'], twitter_keys['consumer_secret'])
    auth.set_access_token(twitter_keys['access_token_key'], twitter_keys['access_token_secret'])
    
    return auth

def tweet_results(status_text=DEFAULT_TWEET_TEXT):
    auth = get_auth()
    api = tweepy.API(auth)
    
    try:
        media = api.media_upload(IMAGE_FILENAME)
        api.update_status(status=status_text, media_ids=[media.media_id]) 
    except Exception as e:
        print(e) 

def lambda_handler(event, context):
    
    s3 = boto3.client("s3", aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_ACCESS_KEY)
    
    try:
        s3.head_object(Bucket=SOURCE_BUCKET_NAME, Key='results.csv')
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            return { 'message': 'File doesn\'t exist in S3 bucket.'}
        else:
            return { 'message': 'Something went wrong.'}
        
    s3.download_file(SOURCE_BUCKET_NAME, 'results.csv', '/tmp/results.csv')
    results_df = pd.read_csv('/tmp/results.csv', sep = ',', header=0)
    
    result = results_df.to_json(orient="records")
    
    parsed = json.loads(result)

    parsed.sort(key=lambda x: x["risk_by_sentiment_analysis"], reverse=True)
    parsed = parsed[0:10]
    parsed.reverse()
    
    y =  [elem['vendor'] for elem in parsed]
    x = [elem['risk_by_sentiment_analysis'] for elem in parsed]
    yText = [str(elem['risk_by_sentiment_analysis']) for elem in parsed]
    dateValue = datetime.datetime.now()

    fig = go.Figure(go.Bar(
            x= x,
            y= y,
            orientation = 'h',
            text = yText,
            textposition= 'auto',
            hoverinfo= 'none'))

    fig.update_layout(
        autosize=False,
        width=1600,
        height=900)

    fig.update_layout(
        xaxis_title="Vulnerability risk", 
        yaxis_title="Vendor")

    fig.update_layout(
        title_text="Top High-Security Risk Vendors Based on ML Analysis - { " + str(dateValue.strftime("%B %d %Y")) + " } " 
    )

    fig.write_image(IMAGE_FILENAME) 

    res = s3.upload_file(IMAGE_FILENAME, SOURCE_BUCKET_NAME, 'resultsGraph.png')

    tweet_results()

    return {
        "statusCode": 200,
        "body": "Success",
    }
