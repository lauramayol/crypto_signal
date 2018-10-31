import os
from crypto_track.models import CryptoCandle, PyTrends
import requests
import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
import datetime


def get_nomics(request, query_currency):
    # example request: GET localhost:8000/load/nomics?currency=BTC
    api_key = os.environ["NOMICS_API_KEY"]
    candle_url = "https://api.nomics.com/v1/candles"
    source = f"Nomics {candle_url}"
    interval = "1d"
    currency_quote = "USD"

    api_url = f"{candle_url}?key={api_key}&interval={interval}&currency={query_currency}"

    # Get start and end dates if provided
    final_url = append_optional_params(request, "start", api_url)
    final_url = append_optional_params(request, "end", final_url)

    # Read API
    historical_crypto_results = requests.get(final_url).json()

    CryptoCandle.objects.all().delete()
    x = 0
    for record in historical_crypto_results:
        try:

            db_record = CryptoCandle(currency_traded=query_currency,
                                     currency_quoted=currency_quote, period_interval=interval, period_start_timestamp=record['timestamp'],
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
            append_trend_dates(request, db_record)
            x += 1
    return JsonResponse({"status_code": 202, "status": "Accepted",
                         "message": f"Inserted {x} records on {timezone.now()}."}
                        )


def append_optional_params(request, var_name, url_og):
    '''
        Checks if request is using an optional parameter and appends it to request of the source.
    '''
    var_value = request.GET.get(var_name, '')

    if var_value:
        url_og += f"&{var_name}={var_value}"

    return url_og


def append_trend_dates(request, candle):
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
