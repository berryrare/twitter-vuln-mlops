# #!/usr/bin/env python
# # coding: utf-8

import tweepy
import requests
import os
import sys
from dotenv import load_dotenv

IMAGE_FILENAME = 'vulnerability_data_results.jpg'

def download_image(url):
    filename = IMAGE_FILENAME
    request = requests.get(url, stream=True)
    if request.status_code == 200:
        with open(filename, 'wb') as image:
            for chunk in request:
                image.write(chunk)
    else:
        raise Exception("Unable to download image.") 

def get_auth():
    load_dotenv()
    twitter_keys = {
        'consumer_key': os.getenv('API_KEY'),
        'consumer_secret': os.getenv('API_KEY_SECRET'),
        'access_token_key': os.getenv('ACCESS_TOKEN'),
        'access_token_secret': os.getenv('ACCESS_TOKEN_SECRET'),
        }
    auth = tweepy.OAuthHandler(twitter_keys['consumer_key'], twitter_keys['consumer_secret'])
    auth.set_access_token(twitter_keys['access_token_key'], twitter_keys['access_token_secret'])
    
    return auth
    
def tweet_results(image_url, status_text='Top 10'):
    auth = get_auth()
    api = tweepy.API(auth)
    
    try:
        download_image(image_url)
        media = api.media_upload(IMAGE_FILENAME)
        api.update_status(status=status_text, media_ids=[media.media_id]) 
        os.remove(IMAGE_FILENAME)
    except Exception as e:
        print(e)  

if __name__ == "__main__":
    tweet_results(sys.argv[1])