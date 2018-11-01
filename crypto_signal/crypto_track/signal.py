from crypto_track.models import CryptoCandle, PyTrends
from django.shortcuts import get_object_or_404
from django.utils import timezone
import datetime


class Signal():

    def __init__(self,
                 currency,
                 currency_quoted="USD",
                 period_interval="1d",
                 data_source_short="Nomics"
                 ):
        '''
            Attributes (align with CryptoCandle model):
            currency (str): cryptocurrency being tracked
            currency_quoted (str): currency used for the prices. Default = USD
            period_interval (str): Time interval of the candle. Default 1d = 1 day (daily)
            data_source_short (str): short version of data source field from CryptoCandle model. Default = Nomics
        '''
        self.currency = currency
        self.currency_quoted = currency_quoted
        self.period_interval = period_interval
        self.data_source_short = data_source_short

        # specify the subset we will be working with
        # sort by timestamp descending
        self.candle_subset = CryptoCandle.objects.filter(currency_traded=self.currency,
                                                         currency_quoted=self.currency_quoted,
                                                         period_interval=self.period_interval,
                                                         search_trend__isnull=False,
                                                         data_source__contains=self.data_source_short
                                                         )

    def get_signal(self, search_date):
        '''
            Retrieves CryptoCandle object based on class parameters and date.
        '''

        # date is not required, if user does not specify then we provide the latest
        if search_date == "":
            my_candle = self.candle_subset.order_by('-period_start_timestamp')[0]
        else:
            my_candle = get_object_or_404(self.candle_subset,
                                          search_trend__date=search_date
                                          )

        return_message = {"currency": candle.currency_traded,
                          "currency_quoted": candle.currency_quoted,
                          "date": candle.search_trend.date,
                          "timestamp": candle.period_start_timestamp,
                          "period_close": candle.period_close,
                          "prior_period_close": candle.prior_period_candle.period_close,
                          "trend_ratio": candle.search_trend.trend_ratio,
                          "signal": candle.signal,
                          }
        return return_message

    def update_signal(self):
        '''
            Loops through candle subset to update signal and bank estimates. One-time update each time the data sources are updated.
            TODO (reminder): allow optional start/end date parameters
        '''
        # initiate variables to be used in loop
        prior_candle = ""
        x = 0
        buy_switch = ""
        # below i want to make sure my delta is working along with my period interval. This will need to be updated once we introduce hourly intervals.
        if self.period_interval == "1d":
            delta_requirement == 1

        # clear the fields before updating them
        self.candle_subset.update(signal__isnull=True, prior_period_candle__isnull=True, bank__isnull=True)

        for candle in self.candle_subset.order_by('period_start_timestamp'):
            # make sure that we have a candle instance to compare against
            if prior_candle:
                candle_delta = candle.search_trend.date - prior_candle.search_trend.date
                # Make sure the two objects meet delta requirements
                if candle_delta.days == delta_requirement:
                    result = self.calculate_signal(candle, prior_candle)
                    # counting our success instances
                    if result:
                        x += 1
                        # simulate our bank
                        # if candle.signal == "BUY" and buy_switch != "BUY":
                        #     buy_switch = candle.signal
                        #     bank

            curr_candle = candle

        return f"Inserted {x} records on {timezone.now()}."

    def calculate_signal(self, candle, compare_candle):
        '''
            Updates attributes "signal" and "prior_period_candle" of "candle" instance individually.
        '''
        # default values
        trend_ratio_default = 0.35
        price_diff_default = 80

        # get price difference
        price_diff = candle.period_close - compare_candle.period_close
        my_trend_ratio = candle.search_trend.trend_ratio

        if my_trend_ratio > trend_ratio_default and price_diff > price_diff_default:
            calc_signal = "BUY"
        else:
            calc_signal = "SELL"

        candle.signal = calc_signal
        candle.prior_period_candle = compare_candle
        candle.save()
        return True
