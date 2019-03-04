import os
from crypto_track.models import CryptoCandle, PyTrends
import requests
import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
import pytz
import datetime
import pandas as pd
from pandas.io.json import json_normalize


class CryptoData():
    '''
        Attributes (align with CryptoCandle model):
            Required:
                currency (str): cryptocurrency being tracked
            Optional:
                currency_quoted (str): currency used for the prices. Default = USD
                period_interval (str): Time interval of the candle. Default 1d = 1 day (daily)
    '''

    def __init__(self,
                 currency,
                 request=None,
                 currency_quoted="USD",
                 period_interval="1d"
                 ):

        self.request = request
        self.currency = currency
        self.currency_quoted = currency_quoted
        self.period_interval = period_interval

    def get_nomics(self):
        # example request: GET localhost:8000/load/nomics?currency=BTC
        api_key = os.environ["NOMICS_API_KEY"]
        candle_url = "https://api.nomics.com/v1/candles"
        source = f"Nomics {candle_url}"

        api_url = f"{candle_url}?key={api_key}&interval={self.period_interval}&currency={self.currency}"

        # Get start and end dates if provided
        final_url = self.append_optional_params("start", api_url)
        final_url = self.append_optional_params("end", final_url)

        # Read API
        historical_crypto_results = requests.get(final_url).json()

        # Convert to dataframe so we can get the min date value
        historical_df = json_normalize(historical_crypto_results)
        # Get the datetime value of the first candle that Nomics has sent us.
        first_candle = historical_df.timestamp.min()

        #first_candle = pd.to_datetime(first_candle, errors='coerce')

        CryptoCandle.objects.filter(crypto_traded=self.currency,
                                    currency_quoted=self.currency_quoted,
                                    period_interval=self.period_interval,
                                    period_start_timestamp__gte=first_candle).delete()
        x = 0
        for record in historical_crypto_results:
            try:

                db_record = CryptoCandle(crypto_traded=self.currency,
                                         currency_quoted=self.currency_quoted,
                                         period_interval=self.period_interval,
                                         period_start_timestamp=record['timestamp'],
                                         period_low=float(record['low']),
                                         period_open=float(record['open']),
                                         period_close=float(record['close']),
                                         period_high=float(record['high']),
                                         period_volume=float(record['volume']),
                                         data_source=source
                                         )

            except Exception as exc:
                return JsonResponse({"status_code": 409,
                                     "status": "Conflict",
                                     "type": type(exc).__name__,
                                     "message": exc.__str__()})

            else:
                db_record.save()
                self.append_trend_dates(db_record)
                x += 1
        return JsonResponse({"status_code": 202, "status": "Accepted",
                             "message": f"Inserted {x} records on {timezone.now()}."}
                            )

    def append_optional_params(self, var_name, url_og):
        '''
            Checks if request is using an optional parameter and appends it to request of the source.
        '''
        var_value = self.request.GET.get(var_name, '')

        if var_value:
            url_og += f"&{var_name}={var_value}"

            if var_value in ['start', 'end']:
                url_og += 'T00%3A00%3A00Z'

        return url_og

    def append_trend_dates(self, candle):
        '''
            Appends foreign key of PyTrends unto Candle instance.
        '''

        date_converted = datetime.datetime.strptime(candle.period_start_timestamp[:19], '%Y-%m-%dT%H:%M:%S')

        try:
            # For daily candles we will strip the time and join on date().
            if self.period_interval == '1d':
                my_trend = get_object_or_404(PyTrends,
                                             date__date=date_converted.date(),
                                             period_interval=self.period_interval
                                             )
            # For hourly candles we will adjust candle timezone from local Eastern because it is based on where you are pulling data.
            elif self.period_interval == '1h':
                my_trend = get_object_or_404(PyTrends,
                                             date=timezone.make_aware(date_converted, timezone=pytz.timezone('UTC')),
                                             period_interval=self.period_interval
                                             )

        except:
            return False
        else:
            candle.search_trend = my_trend
            candle.save()
            return True
