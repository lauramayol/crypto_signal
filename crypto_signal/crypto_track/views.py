
from django.http import JsonResponse
from django.utils import timezone
import datetime
from crypto_track.trends import CryptoTrends
from crypto_track.models import CryptoCandle
from crypto_track.signal import Signal
from . import crypto_data
from crypto_track.track_exception import TrackException


def signal(request):
    '''
        # example request: GET localhost:8000/signal?currency=BTC&date=yyyy-mm-dd

        Variables:
        currency (str) =
        date (str) = date of signal

        Return value:
        Returns buy or sell of currency queried for a given date, starting from 2013 up to today. If no date is given, latest available is returned.
    '''
    # initialize variable
    search_date = ""

    try:
        # Get currency from request
        user_currency = request.GET.get('currency', '')
        # currency is required to be given in request.
        if user_currency == "":
            raise TrackException("Please specify a currency in your request.", "Bad Request")
        my_signal = Signal(user_currency)

        # Get date from request. Date is optional
        user_date = request.GET.get('date', search_date)

        if user_date != "":
            search_date = datetime.datetime.strptime(user_date, '%Y-%m-%d')

        return_message = my_signal.get_signal(search_date)
    except Exception as exc:
        return JsonResponse({"status_code": 409,
                             "status": "Conflict",
                             "type": type(exc).__name__,
                             "message": exc.__str__()})
    else:
        return JsonResponse(return_message)


def load_nomics(request):
    # example request: POST localhost:8000/load/nomics?currency=BTC
    try:
        query_currency = request.GET.get('currency', '')
        if query_currency == "" or request.method != "POST":
            raise Exception()
    except:
        return JsonResponse({"status_code": 400, "status": "Bad Request",
                             "message": "Please submit a valid request."})
    else:
        return_message = crypto_data.get_nomics(request, query_currency)

    return return_message


def load_kaggle(request):
    pass


def load_ccxt(request):
    pass


def load_trends(request):
    '''
        Used to populate PyTrends model from Google Trend data.
        sample: POST localhost:8000/load/trends
    '''
    if request.method == "POST":
        my_trend = CryptoTrends('buy bitcoin', 'BTC USD')

        end_date = datetime.datetime.now().date()
        start_date = end_date - datetime.timedelta(days=180)

        # Iterate over a 6 month period because model will aggregate the dates to weekly summary if we try to pull a longer timespan.
        while end_date.year >= 2013:
            # We do not need any data before 2013, this is how far our historical data for bitcoin spans.
            if start_date < datetime.date(2013, 1, 1):
                start_date = datetime.date(2013, 1, 1)

            try:
                # Load google trend data into database.
                status_message = my_trend.load_model(f"{start_date} {end_date}")
            except Exception as exc:
                return JsonResponse({"status_code": 409,
                                     "status": "Conflict",
                                     "type": type(exc).__name__,
                                     "message": exc.__str__()})
            else:
                # re-assign start and end dates to shift 6 months backwards.
                end_date = start_date - datetime.timedelta(days=1)
                start_date = start_date - datetime.timedelta(days=180)

        return JsonResponse({"status_code": 202, "status": status_message})
    else:
        return JsonResponse({"status_code": 400, "status": "Bad Request",
                             "message": "Please submit a valid request."})


def update_candles(request):
    '''
        Updates search_trend for all candle data. We can use this if we have already loaded candle data but need to update the trend relationship on its own.
        sample: PATCH localhost:8000/update/candles
    '''
    if request.method == "PATCH":
        x = 0
        for candle in CryptoCandle.objects.all():
            find_trend = crypto_data.append_trend_dates(request, candle)
            if find_trend:
                x += 1

        return JsonResponse({"status_code": 202, "status": "Accepted",
                             "message": f"Updated {x} records on {timezone.now()}."}
                            )
    else:
        return JsonResponse({"status_code": 400, "status": "Bad Request",
                             "message": "Please submit a valid request."})
