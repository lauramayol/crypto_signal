import os
from crypto_track.models import CryptoCandle, PyTrends
import requests
import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
import datetime


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

        CryptoCandle.objects.filter(crypto_traded=self.currency,
                                    currency_quoted=self.currency_quoted,
                                    period_interval=self.period_interval).delete()
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

        return url_og

    def append_trend_dates(self, candle):
        '''
            Appends foreign key of PyTrends unto Candle instance.
        '''
        date_converted = datetime.datetime.strptime(candle.period_start_timestamp[:10], '%Y-%m-%d')
        try:
            my_trend = get_object_or_404(PyTrends, pk=date_converted)
        except:
            return False
        else:
            candle.search_trend = my_trend
            candle.save()
            return True
