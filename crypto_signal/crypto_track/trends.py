from pytrends.request import TrendReq
from crypto_track.models import PyTrends
import datetime
from django.http import JsonResponse
from django.utils import timezone
import pytz


class CryptoTrends:

    def __init__(self, search_val1, search_val2, period_interval='1d'):
        '''
            Attributes:
            search_val1 (str): first search string to track using Google Trends
            search_val2 (str): second search string to track using Google Trends
        '''
        self.search_val1 = search_val1
        self.search_val2 = search_val2
        self.period_interval = period_interval

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

    def load_single_period(self, period):
        '''
            Loads data model PyTrends within SQL database.
        '''
        df = self.get_trends(period)
        for index, row in df.iterrows():
            trend_record = PyTrends(date=timezone.make_aware(index,timezone='GMT-4'),
                                    period_interval=self.period_interval,
                                    buy_bitcoin=row[self.search_val1],
                                    btc_usd=row[self.search_val2],
                                    is_partial=row['isPartial']
                                    )
            if abs(trend_record.btc_usd) > 0:
                trend_record.trend_ratio = trend_record.buy_bitcoin / trend_record.btc_usd
            trend_record.save()
        return "Accepted"

    def load_model(self, initial_start_date=None, initial_end_date=timezone.now().date()):

        # initialize variables for initial period we will load.
        end_date = initial_end_date
        start_date = initial_start_date

        if self.period_interval == '1d':
            # For daily candles, we will load 180 days of trends at a time, ending at 1/1/2013, which is the length of time we have candle data for.
            start_date = start_date or datetime.date(2013, 1, 1)
            step_days = 180
            start_append = ''
            end_append = start_append
        elif self.period_interval == '1h':
            # For hourly candles, we will load 7 days of trends at a time, ending with 30 days from today, which is the length of time we have candle data for.
            start_date = start_date or (end_date - timezone.timedelta(days=30))
            step_days = 6
            start_append = 'T0'
            # If end_date is today or in the future, we end parameter with current hour.
            if end_date >= timezone.now().date():
                end_append = 'T' + str(timezone.now().hour)
            else:
                end_append = 'T23'

        step_interval = timezone.timedelta(days=step_days)

        interval_start_date = end_date - step_interval

        #print('before UTC', start_date)
        #start_date = timezone.make_aware(start_date)
        #print('after UTC', start_date)
        PyTrends.objects.filter(date__gte=start_date,
                                date__lt=end_date + timezone.timedelta(days=1),
                                period_interval=self.period_interval).delete()
        # Iterate over a 6 month period because model will aggregate the dates to weekly summary if we try to pull a longer timespan.
        while end_date >= start_date:
            # We do not need any data before 2013, this is how far our historical data for bitcoin spans.
            if interval_start_date < start_date:
                interval_start_date = start_date
            # Load google trend data into database.
            status_message = self.load_single_period(f"{interval_start_date}{start_append} {end_date}{end_append}")
            # Moving forward we will end our period at the end of the day.
            if self.period_interval == '1h':
                end_append = 'T23'

            # re-assign start and end dates to shift based on step_interval, backwards.
            end_date = interval_start_date - timezone.timedelta(days=1)
            interval_start_date = interval_start_date - step_interval

        return status_message
