#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import os.path
from TwitterRetriever import TwitterRetriever
from SentimentAnalyzer import SentimentAnalyzer
from tqdm import tqdm
from datetime import datetime, timedelta

tqdm.pandas()

class RiskAssessor:
    def __init__(self, twitter_retriever, vendors_list, keywords_list, latest = True):
        self.twitter_retriever = twitter_retriever 
        self.vendors = [vendor.lower() for vendor in vendors_list] 
        self.keywords = [keyword.lower() for keyword in keywords_list] 
        self.tweets = self.__get_tweets(latest)
        self.tweet_counts = self.__get_tweets_count_as_df()
        self.sentiment_analyzer = SentimentAnalyzer(self.tweets)
    
    def __get_tweets(self, latest):
        df = pd.DataFrame()
        if (latest == True):
            if (self.twitter_retriever.premium and os.path.isfile('/tmp/tweets.csv')):
                    current_tweets = pd.read_csv('/tmp/tweets.csv')
                    most_recent_id = current_tweets.tweet_id.max()
                    most_recent_tweets = self.twitter_retriever.get_tweets(self.vendors, self.keywords, since_id = most_recent_id)
                    df = self.__get_tweets_for_last_n_days(current_tweets, most_recent_tweets)
            else:
                    df = self.twitter_retriever.get_tweets(self.vendors, self.keywords)
            df.to_csv('/tmp/tweets.csv', index = False)
        elif (os.path.isfile('/tmp/tweets.csv')):
            return pd.read_csv('/tmp/tweets.csv')
        
        return df    
    
    def __get_tweets_for_last_n_days(self, current_tweets, most_recent_tweets, n = 30):
        n_days_ago = (datetime.now() - timedelta(days = n)).strftime('%Y-%m-%d %H:%M:%S+00:00')
        current_tweets = current_tweets[current_tweets['tweet_created_at'] > n_days_ago]
        result = pd.concat([current_tweets, most_recent_tweets])
        result = result.reset_index(drop = True)
        
        return result

        
    def __get_tweets_count_as_df(self):
        df = self.tweets.groupby(['vendor']).size().to_frame(name = 'tweet_count').reset_index()
        df.vendor = df.vendor.apply(lambda string: string.lower())
        
        return df
    
    def __get_number_of_cybersecurity_related_tweets(self):
        return self.twitter_retriever.get_tweets_count_for_keywords(self.keywords)
    
    def __get_number_of_tweets_by_vendor(self, vendor):
        return self.twitter_retriever.get_tweets_count_for_keywords([vendor])
    
    def __get_number_of_cybersecurity_tweets_by_vendor(self, vendor):
        tweet_counts_df = self.__get_tweets_count_as_df()
        vendor = vendor.lower()
        if (vendor in tweet_counts_df.vendor.values):
            return tweet_counts_df[tweet_counts_df.vendor == vendor]['tweet_count'].iloc[0]    
        else: 
            if (vendor in self.vendors):
                return 0
            else:
                raise Exception('Unknown. No data collected for this vendor.')

    def __get_risk_rank_label(self, tweet_count):
        quartile_1 = self.tweet_counts.describe().loc['25%'].iloc[0]
        quartile_3 = self.tweet_counts.describe().loc['75%'].iloc[0]
        
        if (tweet_count <= quartile_1):
            return 'low'
        if (tweet_count >= quartile_3):
            return 'high'
        return 'medium'
        
    def get_relative_vendor_risk_rank(self, vendor):
        cybersecurity_tweet_count_for_vendor = self.__get_number_of_cybersecurity_tweets_by_vendor(vendor)

        return self.__get_risk_rank_label(cybersecurity_tweet_count_for_vendor)
    
    def get_relative_vendor_risk(self, vendor, consider_vendor_popularity = False):
        cybersecurity_tweet_count_for_vendor = self.__get_number_of_cybersecurity_tweets_by_vendor(vendor)
        total_relative_tweet_count = self.tweet_counts['tweet_count'].sum()
        
        vendor_risk = cybersecurity_tweet_count_for_vendor * 100 / total_relative_tweet_count
        
        if (consider_vendor_popularity == True):
            if (self.twitter_retriever.premium):
                return float('NaN')
            total_tweet_count_for_vendor = self.__get_number_of_tweets_by_vendor(vendor)
            chance_of_cybersecurity_tweet_if_vendor = cybersecurity_tweet_count_for_vendor * 100 / total_tweet_count_for_vendor
            vendor_risk = (vendor_risk + chance_of_cybersecurity_tweet_if_vendor) / 2
                    
        return round(vendor_risk, 2)
        
    def get_absolute_vendor_risk(self, vendor, consider_vendor_popularity = False):
        if (self.twitter_retriever.premium):
            return float('NaN')
        cybersecurity_tweet_count_for_vendor = self.__get_number_of_cybersecurity_tweets_by_vendor(vendor)
        total_cybersecurity_tweet_count = self.__get_number_of_cybersecurity_related_tweets()
        
        vendor_risk = cybersecurity_tweet_count_for_vendor * 100 / total_cybersecurity_tweet_count 
        
        if (consider_vendor_popularity == True):
            total_tweet_count_for_vendor = self.__get_number_of_tweets_by_vendor(vendor)
            chance_of_cybersecurity_tweet_if_vendor = cybersecurity_tweet_count_for_vendor * 100 / total_tweet_count_for_vendor
            vendor_risk = (vendor_risk + chance_of_cybersecurity_tweet_if_vendor) / 2
                    
        return round(vendor_risk, 2)
    
    def get_vendor_risk_by_sentiment_analysis(self, vendor):
        cybersecurity_tweet_count_for_vendor = self.__get_number_of_cybersecurity_tweets_by_vendor(vendor)
        negative_sentiment_count = self.sentiment_analyzer.get_sentiment_count_for_vendor(vendor, 'neg')
        mean_negative_magnitude = self.sentiment_analyzer.get_mean_sentiment_magnitude_for_vendor(vendor, 'neg')
        
        if negative_sentiment_count == 0:
            return 0.00

        vendor_risk = mean_negative_magnitude * negative_sentiment_count * 100 / cybersecurity_tweet_count_for_vendor
        
        return round(vendor_risk, 2)