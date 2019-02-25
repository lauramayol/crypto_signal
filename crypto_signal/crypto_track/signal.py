from crypto_track.models import CryptoCandle, SignalSimulation, Simulation, CryptoProphet
from django.shortcuts import get_object_or_404
from django.utils import timezone
from crypto_track.transaction import BankTransaction
from crypto_track.stocker import Stocker
import pandas


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
        self.prediction_days = 90

        # specify the subset we will be working with
        # remove search_trend filter if we choose to not use Google Trends
        self.candle_subset = CryptoCandle.objects.filter(crypto_traded=self.currency,
                                                         currency_quoted=self.currency_quoted,
                                                         period_interval=self.period_interval,
                                                         data_source__contains=self.data_source_short
                                                         )
        self.simulation_obj = get_object_or_404(Simulation, pk=self.simulation_id)

    def get_signal(self, search_date):
        '''
            Retrieves CryptoCandle object based on class parameters and date.
        '''

        # date is not required, if user does not specify then we provide the latest
        if search_date:
            my_candle = get_object_or_404(self.candle_subset,
                                          period_start_timestamp__startswith=search_date
                                          )
            # Check if there is a signal for th specified date
            try:
                my_signal = get_object_or_404(SignalSimulation,
                                              crypto_candle=my_candle,
                                              simulation=self.simulation_obj)
            # We will still return a record if there is no signal because the user wants to see the data for a specific date. Signal details will just be blank.
            except:
                my_signal = None
                comparison_period_date = None
                comparison_period_close = None
                trend_ratio = None
                simulation_name = None
                signal = None
        # When there is no date specified, we will just get the latest Signal we have available.
        else:
            signal_subset = SignalSimulation.objects.filter(simulation=self.simulation_obj,
                                                            signal__isnull=False,
                                                            crypto_candle__crypto_traded=self.currency,
                                                            crypto_candle__currency_quoted=self.currency_quoted,
                                                            crypto_candle__period_interval=self.period_interval,
                                                            crypto_candle__data_source__contains=self.data_source_short
                                                            )
            my_signal = signal_subset.order_by('-crypto_candle__period_start_timestamp')[0]
            my_candle = my_signal.crypto_candle

        if my_signal:
            comparison_period_date = my_signal.candle_compare.period_start_timestamp[:10]
            comparison_period_close = my_signal.candle_compare.period_close
            simulation_name = my_signal.simulation.name
            signal = my_signal.signal
            if my_candle.search_trend:
                trend_ratio = my_candle.search_trend.trend_ratio
            else:
                trend_ratio = None

        return_message = {"currency": my_candle.crypto_traded,
                          "currency_quoted": my_candle.currency_quoted,
                          "date": my_candle.period_start_timestamp[:10],
                          "timestamp": my_candle.period_start_timestamp,
                          "period_close": my_candle.period_close,
                          "comparison_period_date": comparison_period_date,
                          "comparison_period_close": comparison_period_close,
                          "trend_ratio": trend_ratio,
                          "simulation_name": simulation_name,
                          "signal": signal,
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
        conditional_message = ''

        # Next, delete the existing simulation
        SignalSimulation.objects.filter(simulation=self.simulation_obj,
                                        crypto_candle__crypto_traded=self.currency).delete()

        # The only time we want to see the future first is when we are determining hindsight simulations.
        if self.simulation_id in [2, 4, 5]:
            loop_candles = self.candle_subset.order_by('-period_start_timestamp')
            if self.simulation_id in [4, 5]:
                conditional_message += ' ' + self.predict_price()
        else:
            loop_candles = self.candle_subset.filter(search_trend__isnull=False).order_by('period_start_timestamp')

        for candle in loop_candles:
            # For initial candle, we will initialize the simulation and bank and do nothing else.
            if prior_candle is None:
                my_sim = SignalSimulation(crypto_candle=candle,
                                          simulation=self.simulation_obj
                                          )
                my_sim.save()

            else:
                days_diff = 0
                if candle.search_trend and prior_candle.search_trend:
                    candle_delta = candle.search_trend.date - prior_candle.search_trend.date
                    days_diff = candle_delta.days

                # below i want to make sure my delta is working along with my period interval. This will need to be updated once we introduce hourly intervals.
                if ((self.period_interval == "1d" and days_diff == 1) or self.simulation_id in [2, 4, 5]):

                    sim_result = self.calculate_signal(candle, prior_candle)
                    # counting our success instances
                    if sim_result:
                        x += 1
            prior_candle = candle

        # Once we have updated all signals, we can model transaction history.
        transaction_sim = BankTransaction(self.candle_subset, self.simulation_obj, self.currency)
        transaction_sim.transaction_history()

        return f"Inserted {x} signal records on {timezone.now()}.{conditional_message}"

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
        elif self.simulation_id == 5:
            calc_signal = self.calculate_signal_prophet(compare_candle)
            # Signal #5 is almost equivalent to #4 but takes into account Google Trend ratio
            if candle.search_trend:
                if candle.search_trend.trend_ratio and candle.search_trend.trend_ratio > 0.35:
                    calc_signal = "BUY"
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
        if candle.search_trend:
            my_trend_ratio = candle.search_trend.trend_ratio
        else:
            my_trend_ratio = None
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
        try:
            my_prophet = get_object_or_404(CryptoProphet,
                                           crypto_candle=next_candle,
                                           simulation=self.simulation_obj)
        except:
            calc_signal = "HOLD"

        else:
            if float(my_prophet.change) < 0:
                calc_signal = "SELL"
            elif float(my_prophet.change) > 0:
                calc_signal = "BUY"
            else:
                # Hold signal from prior day. Note: Since ideally we do not want HOLD, need to update code to copy BUY/SELL from prior day.
                calc_signal = "HOLD"

        return calc_signal

    def predict_price(self):
        # Initialize Stocker object
        crypto_stocker = Stocker(ticker=self.currency, currency_quoted=self.currency_quoted)

        # Change defaults as analyzed in Stocker Prediction Usage.ipynb notebook.
        crypto_stocker.training_years = 6
        crypto_stocker.weekly_seasonality = True
        crypto_stocker.changepoint_prior_scale = 0.4
        # Create predictions
        future, train, model = crypto_stocker.predict_future_df(self.prediction_days)

        # Create predictions and load table.
        return_message = self.dbload_prophet(df=future, object_type='CryptoCandle.period_close')

        return return_message

    def dbload_prophet(self, df, object_type):
        '''
            Loads given pandas dataframe (df) into CryptoProphet model in database.
        '''

        # Loop through data to create database record,
        for index, row in df.iterrows():
            # Delete if unique record exists
            CryptoProphet.objects.filter(
                date=row['ds'],
                object_type=object_type,
                simulation=self.simulation_obj,
                crypto_traded=self.currency,
                currency_quoted=self.currency_quoted,
                period_interval=self.period_interval
            ).delete()
            # Check to see if we have an existing CryptoCandle object so we can reference with ForeignKey
            try:
                candle = CryptoCandle.objects.get(
                    search_trend__date=row['ds'],
                    currency_quoted=self.currency_quoted,
                    period_interval=self.period_interval,
                    crypto_traded=self.currency)
            except:
                candle = None

            prophet_record = CryptoProphet(date=row['ds'],
                                           object_type=object_type,
                                           simulation=self.simulation_obj,
                                           crypto_traded=self.currency,
                                           currency_quoted=self.currency_quoted,
                                           period_interval=self.period_interval,
                                           metric_value=row['yhat'],
                                           upper=row['yhat_upper'],
                                           lower=row['yhat_lower'],
                                           change=row['diff'],
                                           crypto_candle=candle
                                           )
            prophet_record.save()
        return f"Loaded {df.ds.count()} predictions."

    def predict_trend(self):
        object_type = 'PyTrends.trend_ratio'

        # Pull and prep data
        conn = sqlite3.connect("db.sqlite3")
        df = pd.read_sql_query("select date as ds, btc_usd, buy_bitcoin, trend_ratio from crypto_track_pytrends;", conn)
        df['y'] = df['trend_ratio']
        df['ds'] = pd.to_datetime(df['ds'], errors='coerce')

        # Get prior 'y' value to fill in nan
        df['y-1'] = df.y.shift(1)
        df['y_nan'] = df.y.isna()
        df.y.fillna(df['y-1'], inplace=True)
        df.drop(['y-1'], axis=1, inplace=True)

        # Instantiate a Prophet object
        future_trend = Prophet(df, 'Trend Ratio')
        # Change default attributes as analyzed in Trend Prediction.ipynb notebook.
        future_trend.weekly_seasonality = True
        future_trend.training_years = 6
        future_trend.changepoint_prior_scale = 0.05

        future, train, model = future_trend.predict_future_df(days)

        # Create predictions and load table.
        return_message = self.dbload_prophet(df=future, object_type=object_type)

        return return_message
