from crypto_track.models import CryptoCandle, PyTrends, Bank
from django.shortcuts import get_object_or_404
from django.utils import timezone
import datetime
import decimal
from django.contrib.auth import get_user_model


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
        self.candle_subset = CryptoCandle.objects.filter(crypto_traded=self.currency,
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

        return_message = {"currency": my_candle.crypto_traded,
                          "currency_quoted": my_candle.currency_quoted,
                          "date": my_candle.search_trend.date,
                          "timestamp": my_candle.period_start_timestamp,
                          "period_close": my_candle.period_close,
                          "prior_period_close": my_candle.prior_period_candle.period_close,
                          "trend_ratio": my_candle.search_trend.trend_ratio,
                          "signal": my_candle.signal,
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
        buy_switch = "SELL"
        # for now, we are just trading with "admin" money
        trader_name = "admin"
        trader = get_user_model().objects.get_or_create(username=trader_name)[0]
        # below i want to make sure my delta is working along with my period interval. This will need to be updated once we introduce hourly intervals.
        if self.period_interval == "1d":
            delta_requirement = 1
        # clear the fields before updating them
        self.candle_subset.update(signal=None, prior_period_candle=None)

        for candle in self.candle_subset.order_by('period_start_timestamp'):
            # For initial candle, we will initialize the bank and do nothing else.
            if prior_candle == "":
                Bank.objects.filter(crypto_candle=candle, user=trader).delete()
                my_bank = Bank(crypto_candle=candle,
                               user=trader,
                               crypto_bank=0.0,
                               cash_bank=decimal.Decimal(1.0))
            # Make sure we have required values to calculate signal: (1) a candle instance to compare against, (2) trend ratio to compare
            elif candle.search_trend.trend_ratio:
                candle_delta = candle.search_trend.date - prior_candle.search_trend.date
                # Make sure the two objects meet delta requirements
                if candle_delta.days == delta_requirement:

                    result = self.calculate_signal(candle, prior_candle)
                    # counting our success instances
                    if result:
                        x += 1
                        # simulate our bank
                        my_bank_results = self.model_transactions(candle, buy_switch, trader, my_bank)
                        my_bank = my_bank_results[0]
                        buy_switch = my_bank_results[1]
            prior_candle = candle

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

    def model_transactions(self, my_candle, prior_signal, trader, prior_bank):
        '''
            This is a basic model:
            1. Spend full cash_bank at first BUY signal
            2. Sell full crypto_bank at first SELL signal after a BUY.
        '''

        # Delete the object if it already exists, we are re-calculating next
        Bank.objects.filter(crypto_candle=my_candle, user=trader).delete()
        # If current signal as the same as prior, we do not act, so bank will stay the same.
        if prior_signal != my_candle.signal:
            # This means we have cash on hand because prior action was SELL.
            if my_candle.signal == "BUY":
                my_bank = Bank(crypto_candle=my_candle,
                               user=trader,
                               crypto_bank=prior_bank.cash_bank / my_candle.period_close,
                               cash_bank=0.0)
                buy_switch = "BUY"
            elif my_candle.signal == "SELL":
                my_bank = Bank(crypto_candle=my_candle,
                               user=trader,
                               crypto_bank=0.0,
                               cash_bank=prior_bank.crypto_bank * my_candle.period_close)
                buy_switch = "SELL"

        else:
            my_bank = prior_bank
            buy_switch = my_candle.signal

        return (my_bank, buy_switch)
