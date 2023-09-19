#!/usr/bin/env python
# coding: utf-8

import tweepy
import time
import pandas as pd
from tqdm import tqdm
import os
from dotenv import load_dotenv

class TwitterRetriever:
    def __init__(self, premium = False):
        load_dotenv()
        self.premium = premium
        self.client = tweepy.Client(bearer_token = os.getenv('BEARER_TOKEN'))
        self.auth = self.__get_auth()
        self.api = tweepy.API(self.auth, wait_on_rate_limit = True)

    def __get_auth(self):
        twitter_keys = {
            'consumer_key': os.getenv('API_KEY'),
            'consumer_secret': os.getenv('API_KEY_SECRET'),
            'access_token_key': os.getenv('ACCESS_TOKEN'),
            'access_token_secret': os.getenv('ACCESS_TOKEN_SECRET'),
        }
        auth = tweepy.OAuthHandler(twitter_keys['consumer_key'], twitter_keys['consumer_secret'])
        auth.set_access_token(twitter_keys['access_token_key'], twitter_keys['access_token_secret'])
        
        return auth
        
    def __turn_into_hashtags(self, word):
        return '#{0}'.format(word)

    def __get_query_based_on_vendor_and_keywords_list(self, vendor, keywords_list):
        query_string = ''
        if (len(vendor) > 0):
            vendor_hashtag = self.__turn_into_hashtags(vendor)
            query_string += '({0}) '.format(vendor_hashtag) if (len(keywords_list) > 0) else '{0} '.format(vendor_hashtag)
        if (len(keywords_list) > 0):
            keywords_list = [self.__turn_into_hashtags(keyword) for keyword in keywords_list]
            keywords_hashtags = ' OR '.join(keywords_list)
            query_string += '({0}) '.format(keywords_hashtags) if (len(query_string) > 0) else '{0} '.format(keywords_hashtags)
        if (len(query_string) > 0):
            query_string += '-is:retweet lang:en'
        
        return query_string

    def __get_tweets_by_vendor_and_keywords_list(self, vendor, keywords_list, since_id = None):
        query = self.__get_query_based_on_vendor_and_keywords_list(vendor, keywords_list)
        if (since_id != None or not self.premium):
            response = tweepy.Paginator(self.client.search_recent_tweets, 
                            query = query, 
                            tweet_fields=['created_at'], 
                            max_results = 100, limit = 20, since_id = since_id)
            return response.flatten()
        else:
            return self.api.search_30_day(label = 'prod', query = query)

    def __get_tweets_by_vendor_and_keywords_list_as_df(self, vendor, keywords_list, since_id = None):
        df = pd.DataFrame(columns = ['vendor', 'tweet_id', 'tweet_text', 'tweet_created_at'])
        unfinished = True
        while unfinished:
            try:
                tweets = self.__get_tweets_by_vendor_and_keywords_list(vendor, keywords_list, since_id)
                for tweet in tweets:
                    if (self.premium and since_id == None):
                        tweet = tweet._json
                        df.loc[len(df)] = [vendor, tweet['id'], tweet['text'], tweet['created_at']]
                    else:
                        df.loc[len(df)] = [vendor, tweet.id, tweet.text, tweet.created_at]
                unfinished = False        
            except tweepy.errors.TooManyRequests as e:
                print(e)
                time.sleep(60)
                continue
            except Exception as e:
                print(e)

        return df

    def get_tweets(self, vendors_list, keywords_list, since_id = None):
        dfs = []
        for vendor in tqdm(vendors_list):
                dfs.append(self.__get_tweets_by_vendor_and_keywords_list_as_df(vendor, keywords_list, since_id)) 

        df = pd.concat(dfs, ignore_index = True)
        df = df.drop_duplicates(subset = ['tweet_id', 'tweet_text'], keep = 'first')

        return df
    
    def get_tweets_count_for_keywords(self, keywords_list):
        query = self.__get_query_based_on_vendor_and_keywords_list('', keywords_list)
        response = self.client.get_recent_tweets_count(query, granularity = 'day')
        tweets_count = 0
        for day_data in response.data:
            tweets_count += day_data['tweet_count']

        return tweets_count 