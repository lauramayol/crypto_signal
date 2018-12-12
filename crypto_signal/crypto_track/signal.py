from crypto_track.models import CryptoCandle, SignalSimulation, Simulation, CryptoProphet
from django.shortcuts import get_object_or_404
from django.utils import timezone
from crypto_track.transaction import BankTransaction
from . import crypto_data


class Signal():
    '''
        Attributes (align with CryptoCandle model):
            Required:
                currency (str): cryptocurrency being tracked
                simulation_id (int): specifies which simulation method we are using from Simulation model.
            Optional:
                currency_quoted (str): currency used for the prices. Default = USD
                period_interval (str): Time interval of the candle. Default 1d = 1 day (daily)
                data_source_short (str): short version of data source field from CryptoCandle model. Default = Nomics
    '''

    def __init__(self,
                 currency,
                 simulation_id,
                 currency_quoted="USD",
                 period_interval="1d",
                 data_source_short="Nomics"
                 ):

        self.currency = currency
        self.simulation_id = simulation_id
        self.currency_quoted = currency_quoted
        self.period_interval = period_interval
        self.data_source_short = data_source_short
        self.prediction_days = 30

        # specify the subset we will be working with
        # remove search_trend filter if we choose to not use Google Trends
        self.candle_subset = CryptoCandle.objects.filter(crypto_traded=self.currency,
                                                         currency_quoted=self.currency_quoted,
                                                         period_interval=self.period_interval,
                                                         search_trend__isnull=False,
                                                         data_source__contains=self.data_source_short
                                                         )
        self.simulation_obj = get_object_or_404(Simulation, pk=self.simulation_id)

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

        my_signal = get_object_or_404(SignalSimulation,
                                      crypto_candle=my_candle,
                                      simulation=self.simulation_obj)

        return_message = {"currency": my_candle.crypto_traded,
                          "currency_quoted": my_candle.currency_quoted,
                          "date": my_candle.search_trend.date,
                          "timestamp": my_candle.period_start_timestamp,
                          "period_close": my_candle.period_close,
                          "comparison_period_date": my_signal.candle_compare.search_trend.date,
                          "comparison_period_close": my_signal.candle_compare.period_close,
                          "trend_ratio": my_candle.search_trend.trend_ratio,
                          "simulation_name": my_signal.simulation.name,
                          "signal": my_signal.signal,
                          }
        return return_message

    def update_signal(self):
        '''
            Loops through candle subset to update signal and bank estimates. One-time update each time the data sources are updated.
            TODO (reminder): allow optional start/end date parameters
        '''
        # initiate variables to be used in loop
        prior_candle = None
        x = 0

        # Next, delete the existing simulation
        SignalSimulation.objects.filter(simulation=self.simulation_obj).delete()

        # The only time we want to see the future first is when we are determining hindsight simulations.
        if self.simulation_id in [2, 4]:
            loop_candles = self.candle_subset.order_by('-period_start_timestamp')
            if self.simulation_id == 4:
                crypto_data.predict_price(self.currency, self.prediction_days)
        else:
            loop_candles = self.candle_subset.order_by('period_start_timestamp')

        for candle in loop_candles:
            # For initial candle, we will initialize the simulation and bank and do nothing else.
            if prior_candle is None:
                my_sim = SignalSimulation(crypto_candle=candle,
                                          simulation=self.simulation_obj
                                          )
                my_sim.save()

            else:
                candle_delta = candle.search_trend.date - prior_candle.search_trend.date
                # below i want to make sure my delta is working along with my period interval. This will need to be updated once we introduce hourly intervals.
                if self.period_interval == "1d" and abs(candle_delta.days) == 1:

                    sim_result = self.calculate_signal(candle, prior_candle)
                    # counting our success instances
                    if sim_result:
                        x += 1
            prior_candle = candle

        # Once we have updated all signals, we can model transaction history.
        transaction_sim = BankTransaction(self.candle_subset, self.simulation_obj)
        transaction_sim.transaction_history()

        return f"Inserted {x} records on {timezone.now()}."

    def calculate_signal(self, candle, compare_candle):
        '''
            Creates SignalSimulation object for candle provided.
        '''
        # default values for price difference
        p_default = {1: 80, 3: 0.01}

        if self.simulation_id in [1, 3]:
            calc_signal = self.calculate_signal_v1(candle, compare_candle, p_default[self.simulation_id])
        elif self.simulation_id == 2:
            calc_signal = self.calculate_signal_hindsight(candle, compare_candle.period_close)
        elif self.simulation_id == 4:
            calc_signal = self.calculate_signal_prophet(compare_candle)
        else:
            calc_signal = ""

        my_sim = SignalSimulation(crypto_candle=candle,
                                  simulation=self.simulation_obj,
                                  candle_compare=compare_candle,
                                  signal=calc_signal)
        my_sim.save()

        return my_sim

    def calculate_signal_v1(self, candle, prior_period_candle, price_diff_default, trend_ratio_default=0.35):
        '''
            Calculates Version 1.0 of signal (based on Marc Howard's blog):
            BUY signal:
                1. Search terms of “Buy Bitcoin” to “BTC USD” ratio is higher than 35%.
                2. BTC price difference closes more than $80 above the prior day’s close price.
            SELL signal:
                BUY signal requirements not met.
        '''

        # calculate differences for current candle
        my_changes = self.get_change_in_candle(candle, prior_period_candle)

        price_diff = my_changes[0]
        my_trend_ratio = my_changes[1]

        if my_trend_ratio is None:
            calc_signal = "HOLD"
        elif my_trend_ratio > trend_ratio_default and price_diff > price_diff_default:
            calc_signal = "BUY"
        else:
            calc_signal = "SELL"

        return calc_signal

    def get_change_in_candle(self, candle, prior_period_candle):
        # get price difference
        # for first sim we are using simple substract from prior to current price
        if self.simulation_id == 1:
            price_diff = candle.period_close - prior_period_candle.period_close
        # for #3 sim we are using % difference
        elif self.simulation_id == 3:
            price_diff = (candle.period_close - prior_period_candle.period_close) / prior_period_candle.period_close
        my_trend_ratio = candle.search_trend.trend_ratio

        return price_diff, my_trend_ratio

    def calculate_signal_hindsight(self, candle, next_candle_price):
        '''
            Calculates Hindsight version of signal:
            BUY signal:
                -- Next candle price close is higher (buy before increase).
            SELL signal:
                -- Next candle price close is lower (sell at peak).
        '''
        if candle.period_close > next_candle_price:
            calc_signal = "SELL"
        elif candle.period_close < next_candle_price:
            calc_signal = "BUY"
        else:
            # Hold signal from prior day. Note: Since ideally we do not want HOLD, need to update code to copy BUY/SELL from prior day.
            calc_signal = "HOLD"

        return calc_signal

    def calculate_signal_prophet(self, next_candle):
        print(next_candle)
        my_prophet = get_object_or_404(CryptoProphet,
                                       crypto_candle=next_candle,
                                       simulation=self.simulation_obj)

        print(my_prophet.price_change)
        if float(my_prophet.price_change) < 0:
            calc_signal = "SELL"
        elif float(my_prophet.price_change) > 0:
            calc_signal = "BUY"
        else:
            # Hold signal from prior day. Note: Since ideally we do not want HOLD, need to update code to copy BUY/SELL from prior day.
            calc_signal = "HOLD"

        return calc_signal
