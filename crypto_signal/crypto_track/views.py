
from django.http import JsonResponse
from django.utils import timezone
from django.views import generic
import datetime
from crypto_track.trends import CryptoTrends
from crypto_track.models import CryptoCandle, Simulation
from crypto_track.signal import Signal
from crypto_track.crypto_data import CryptoData
from crypto_track.track_exception import TrackException
from crypto_track.dataexport import DataExport
import pandas as pd

bad_request_default = {"status_code": 400, "status": "Bad Request",
                       "message": "Please submit a valid request."}


class SimulationView(generic.ListView):
    template_name = 'crypto_track/simview.html'
    context_object_name = 'all_sims_list'

    def get_queryset(self):
        return Simulation.objects.order_by('id')


def signal(request, simulation_id):
    '''
        # example request: GET localhost:8000/1/signal?currency=BTC&date=yyyy-mm-dd

        Return value:
        Returns buy or sell of currency queried for a given date, starting from 2013 up to today. If no date is given, latest available is returned.
    '''
    # initialize variable
    search_date = ""

    try:
        # Get currency from request
        user_currency = request.GET.get('currency', '')
        # currency is required to be given in request.
        if user_currency == "" or simulation_id == None:
            raise TrackException("Please specify a simulation ID and currency in your request.", "Bad Request")
        my_signal = Signal(currency=user_currency, simulation_id=simulation_id)

        # Get date from request. Date is optional
        user_date = request.GET.get('date', search_date)

        return_message = my_signal.get_signal(user_date)
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
        return JsonResponse(bad_request_default)
    else:
        my_data = CryptoData(currency=query_currency, request=request)
        return_message = my_data.get_nomics()

    return return_message


def load_ccxt(request):
    # Placeholder
    pass


def load_trends(request):
    '''
        Used to populate PyTrends model from Google Trend data.
        Note: For now we will use google trends for Bitcoin to compare with other currencies as well.
        sample: POST localhost:8000/load/trends?currency=BTC
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

        # whenever we load raw data, we want to update its signal
        update_candles(request)

        return JsonResponse({"status_code": 202, "status": status_message})
    else:
        return JsonResponse(bad_request_default)


def update_candles(request):
    '''
        Updates search_trend for all candle data. We can use this if we have already loaded candle data but need to update the trend relationship on its own.
        sample: PATCH localhost:8000/update/candles?currency=BTC
    '''
    query_currency = request.GET.get('currency', '')

    if request.method in ("POST", "PATCH"):
        x = 0
        for candle in CryptoCandle.objects.all():
            my_data = CryptoData(currency=query_currency, request=request)
            find_trend = my_data.append_trend_dates(candle)
            if find_trend:
                x += 1

        # whenever we load raw data, we want to update its signal
        update_signal(request)
        return JsonResponse({"status_code": 202, "status": "Accepted",
                             "message": f"Updated {x} records on {timezone.now()}."}
                            )
    else:
        return JsonResponse(bad_request_default)


def update_signal(request, simulation_id=""):
    '''
        Updates signal and prior_period_candle for all candle objects. We can use this if we have already loaded candle data but need to update the values on its own.
        Note: simulation_id is optional, if none is given, all Simulations will be re-calculated (should be used when we re-load the source, then we need to re-calculate all Sims).
        sample: PATCH localhost:8000/update/1/signal?currency=BTC
    '''
    if request.method == "PATCH":
        try:
            # initiate variables
            confirm_message = ""
            # Get currency from request
            user_currency = request.GET.get('currency', '')
            # currency is required to be given in request.
            if user_currency == "":
                raise TrackException("Please specify a currency in your request.", "Bad Request")

            else:
                my_signal = Signal(currency=user_currency, simulation_id=simulation_id)
                # Get prediction days from request (this is necessary only starting with sim id 4)
                my_signal.prediction_days = int(request.GET.get('days', '90'))

                confirm_message = my_signal.update_signal()

        except Exception as exc:
            return JsonResponse({"status_code": 409,
                                 "status": "Conflict",
                                 "type": type(exc).__name__,
                                 "message": exc.__str__()})

        else:

            return JsonResponse({"status_code": 202, "status": "Accepted",
                                 "message": confirm_message}
                                )
    else:
        return JsonResponse(bad_request_default)


def load_simulations(request):
    '''
        Accepts a POST request to load crypto_track_simulation table from excel file crypto_signal/crypto_track/CryptoSimulations.xlsx
    '''
    if request.method == "POST":
        # Load list from file
        sim_list = pd.read_csv('crypto_track_Simulation.csv', index_col='id')
        # Sort based on ID
        sim_list = sim_list.sort_values(by=['id'])

        # First, delete all current objects
        Simulation.objects.all().delete()

        # Create a Simulation record for each row in file
        for index, row in sim_list.iterrows():
            sim_record = Simulation(id=index,
                                    name=row['name'],
                                    description=row['description'],
                                    url=row['url']
                                    )
            sim_record.save()

        confirm_message = f"Loaded {sim_list.name.count()} simulations."
        return JsonResponse({"status_code": 202, "status": "Accepted",
                             "message": confirm_message}
                            )
    else:
        return JsonResponse(bad_request_default)


def data_export(request, format='csv'):
    '''
        Accepts a POST or PATCH request to load all django models into flat files. This can be used for many purposes, but initially meant to load Tableau report.
    '''
    if request.method in ["POST", "PATCH"]:
        e = DataExport(format)
        try:
            confirm_message = e.export_all()
        except Exception as exc:
            return JsonResponse({"status_code": 417,
                                 "status": "Expectation Failed",
                                 "type": type(exc).__name__,
                                 "message": exc.__str__()})
        else:
            return JsonResponse({"status_code": 202, "status": "Accepted",
                                 "message": confirm_message}
                                )

    else:
        return JsonResponse(bad_request_default)
