from pytrends.request import TrendReq
import pandas as pd
import sqlite3
from crypto_track.models import PyTrends
from crypto_track.stocker import Prophet


class CryptoTrends:

    def __init__(self, search_val1, search_val2):
        '''
            Attributes:
            search_val1 (str): first search string to track using Google Trends
            search_val2 (str): second search string to track using Google Trends
        '''
        self.search_val1 = search_val1
        self.search_val2 = search_val2

    def get_trends(self, period):
        '''
            Gets raw data from Google Trend's "Interest Over Time" chart for the given period.

            Attributes:
            period (str): the period to evaluate in "Interest Over Time" chart.
        '''
        kw_list = [self.search_val1, self.search_val2]
        pytrends = TrendReq(hl='en - US')
        pytrends.build_payload(kw_list, cat=0, timeframe=period, geo='', gprop='')

        return pytrends.interest_over_time()

    def load_model(self, period):
        '''
            Loads data model PyTrends within SQL database.
        '''
        df = self.get_trends(period)
        for index, row in df.iterrows():
            trend_record = PyTrends(date=index,
                                    buy_bitcoin=row[self.search_val1],
                                    btc_usd=row[self.search_val2],
                                    is_partial=row['isPartial']
                                    )
            if abs(trend_record.btc_usd) > 0:
                trend_record.trend_ratio = trend_record.buy_bitcoin / trend_record.btc_usd
            trend_record.save()
        return "Accepted"
