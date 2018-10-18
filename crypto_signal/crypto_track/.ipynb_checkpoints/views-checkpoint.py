from django.shortcuts import render
from django.http import JsonResponse
import requests
import os
from crypto_track.models import CryptoCandle, PyTrends
from datetime import datetime
from crypto_track.trends import CryptoTrends

# GET localhost:8000/load/nomics?currency=BTC


def load_nomics(request):
    api_key = os.environ["NOMICS_API_KEY"]
    candle_url = "https://api.nomics.com/v1/candles"
    interval = "1d"
    currency_quote = "USD"

    try:
        query_currency = request.GET.get('currency', '')
        if query_currency == "":
            raise Exception()
    except:
        return JsonResponse({"status_code": 400, "status": "Bad Request",
                             "message": "Please submit a valid request."})
    else:
        api_url = f"{candle_url}?key={api_key}&interval={interval}&currency={query_currency}"

        # Get start and end dates if provided
        final_url = append_optional_params(request, "start", api_url)
        final_url = append_optional_params(request, "end", final_url)

        # Read API
        historical_crypto_results = requests.get(final_url).json()
        source = f"Nomics {candle_url}"

        CryptoCandle.objects.all().delete()
        x = 0
        for record in historical_crypto_results:
            try:

                db_record = CryptoCandle(currency_traded=query_currency,
                                         currency_quoted=currency_quote, period_interval=interval, period_start_timestamp=record['timestamp'],
                                         period_low=float(record['low']), period_open=float(record['open']), period_close=float(record['close']), period_high=float(record['high']), period_volume=float(record['volume']), data_source=source
                                         )

            except Exception as exc:
                return JsonResponse({"status_code": 409,
                                     "status": "Conflict",
                                     "type": type(exc).__name__,
                                     "message": exc.__str__()})

            else:
                db_record.save()
                x += 1
        return JsonResponse({"status_code": 202, "status": "Accepted",
                             "message": f"Inserted {x} records on {datetime.now()}."}
                            )


def append_optional_params(request, var_name, url_og):
    var_value = request.GET.get(var_name, '')

    if var_value:
        url_og += f"&{var_name}={var_value}"

    return url_og


def load_kaggle(request):
    pass


def load_ccxt(request):
    pass


def load_trends(request):
