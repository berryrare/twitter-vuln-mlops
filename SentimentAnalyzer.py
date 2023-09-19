#!/usr/bin/env python
# coding: utf-8

import pandas as pd
from transformers import pipeline
from tqdm import tqdm

tqdm.pandas()

class SentimentAnalyzer:
    def __init__(self, df):
        self.df = self.__get_sentiments_and_magnitudes(df)
                
    def __get_sentiments_and_magnitudes(self, df):
        sentiment_analysis = pipeline(model = "finiteautomata/bertweet-base-sentiment-analysis")
        results = df.tweet_text.progress_apply(lambda tweet: sentiment_analysis(tweet))
        results = results.apply(lambda list_like_element: list_like_element[0])
        temp = df.copy()
        temp['sentiment'] = results.apply(lambda result: result['label'])
        temp['sentiment_magnitude'] = results.apply(lambda result: result['score'])
        
        return temp
    
    def get_min_sentiment_magnitude_for_vendor(self, vendor, sentiment):
        sentiment = sentiment.upper()
        if (sentiment == 'NEG' or sentiment == 'NEU'):
            return round(self.df[(self.df.vendor == vendor) & 
                                 (self.df.sentiment == sentiment)]['sentiment_magnitude'].min(), 2)
        return np.nan

    def get_max_sentiment_magnitude_for_vendor(self, vendor, sentiment):
        sentiment = sentiment.upper()
        if (sentiment == 'NEG' or sentiment == 'NEU'):
            return round(self.df[(self.df.vendor == vendor) & 
                                 (self.df.sentiment == sentiment)]['sentiment_magnitude'].max(), 2)
        return np.nan
    
    def get_mean_sentiment_magnitude_for_vendor(self, vendor, sentiment):
        sentiment = sentiment.upper()
        if (sentiment == 'NEG' or sentiment == 'NEU'):
            return round(self.df[(self.df.vendor == vendor) & 
                                 (self.df.sentiment == sentiment)]['sentiment_magnitude'].mean(), 2)
        return np.nan

    def get_sentiment_count_for_vendor(self, vendor, sentiment):
        sentiment = sentiment.upper()
        if (sentiment == 'NEG' or sentiment == 'NEU'):
            return self.df[(self.df.vendor == vendor) & 
                                 (self.df.sentiment == sentiment)]['sentiment_magnitude'].count()
        return np.nan