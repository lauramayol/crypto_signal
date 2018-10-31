from crypto_track.models import CryptoCandle, PyTrends
from django.shortcuts import get_object_or_404
import datetime
from crypto_track.track_exception import TrackException


class Signal():

    def get_latest(self, candle_subset):
        # Get the latest CryptoCandle with search_trend, this assumes that we will have a buy/sell signal for this date.
        my_candle_list = candle_subset.order_by('-search_trend')[0]
        return my_candle_list

    def get_signal(self, currency, search_date):
        # set default values for current test case
        currency_quoted = "USD"
        period_interval = "1d"
        data_source = "Nomics https://api.nomics.com/v1/candles"

        # currency is required to be given in request.
        if currency == "":
            raise TrackException("Please specify a currency in your request.", "Bad Request")
        # specify the subset we will be working with
        my_subset = CryptoCandle.objects.filter(currency_traded=currency,
                                                currency_quoted=currency_quoted,
                                                period_interval=period_interval,
                                                search_trend__isnull=False,
                                                data_source=data_source
                                                )

        # date is not required, if user does not specify then we provide the latest
        if search_date == "":
            my_candle = self.get_latest(my_subset)
        else:
            my_candle = get_object_or_404(my_subset,
                                          search_trend__date=search_date
                                          )
        prior_candle = get_object_or_404(my_subset,
                                         search_trend__date=my_candle.search_trend.date - datetime.timedelta(days=1)
                                         )

        return_message = self.calculate_signal(my_candle, prior_candle)

        return return_message

    def calculate_signal(self, candle, compare_candle):
        # default values
        trend_ratio_default = 0.35
        price_diff_default = 80

        # get price difference
        price_diff = candle.period_close - compare_candle.period_close
        my_trend_ratio = candle.search_trend.trend_ratio

        if my_trend_ratio > trend_ratio_default and price_diff > price_diff_default:
            signal = "BUY"
        else:
            signal = "SELL"

        return_message = {"currency": candle.currency_traded,
                          "currency_quoted": candle.currency_quoted,
                          "date": candle.search_trend.date,
                          "period_close": candle.period_close,
                          "prior_period_close": compare_candle.period_close,
                          "trend_ratio": my_trend_ratio,
                          "signal": signal,
                          }
        return return_message
