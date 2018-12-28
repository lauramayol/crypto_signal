from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class PyTrends(models.Model):
    '''
    Description:
        Obtained from Google Trend's "Interest over time" metric.

    Attributes:
        date (date): date of trend
        buy_bitcoin (int): score for "buy_bitcoin" search term
        btc_usd (int): score for "btc_usd" search term
        is_partial (bool):
        trend_ratio (dec): ratio of buy_bitcoin/btc_usd
    '''
    date = models.DateField(primary_key=True)
    buy_bitcoin = models.IntegerField(null=True)
    btc_usd = models.IntegerField(null=True)
    is_partial = models.BooleanField(default=False)
    trend_ratio = models.DecimalField(max_digits=10, decimal_places=5, null=True)

    def __str__(self):
        return f"{self.date}"


class CryptoCandle(models.Model):
    '''
    Attributes:
        crypto_traded (str): cryptocurrency being tracked
        currency_quoted (str): currency used for the prices
        period_interval (str): Time interval of the candle
        period_start_timestamp (str): Start time of the candle in RFC3339
        search_trend (PyTrend): PyTrend object related to that day (can be null)
        period_low (dec): Lowest price in currency_quoted
        period_open(dec): First trade price in currency_quoted
        period_close (dec): Last trade price in currency_quoted
        period_high (dec): Highest price in currency_quoted
        period_volume (dec): Volume transacted in period interval in currency_quoted
        data_source (str): where we got this data
        update_timestamp (datetime): when record was created in this database

    '''
    crypto_traded = models.CharField(max_length=3)
    currency_quoted = models.CharField(max_length=3)
    period_interval = models.CharField(max_length=3)
    period_start_timestamp = models.CharField(max_length=50)
    search_trend = models.ForeignKey(PyTrends,
                                     to_field='date',
                                     on_delete=models.SET_NULL,
                                     null=True
                                     )
    period_low = models.DecimalField(max_digits=25, decimal_places=10)
    period_open = models.DecimalField(max_digits=25, decimal_places=10)
    period_close = models.DecimalField(max_digits=25, decimal_places=10)
    period_high = models.DecimalField(max_digits=25, decimal_places=10)
    period_volume = models.DecimalField(max_digits=25, decimal_places=10)
    data_source = models.CharField(max_length=255)
    update_timestamp = models.DateTimeField(default=timezone.now())

    def __str__(self):
        return f"{self.crypto_traded} | {self.period_start_timestamp} | {self.data_source} | Period Close: {self.period_close}"


class Simulation(models.Model):
    '''
        Attritbutes:
            name (str): short name of signal simulation.
            descrition (str): long description of simulation.
    '''

    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=300)
    url = models.CharField(max_length=300, null=True)

    def __str__(self):
        return f"{self.id} | {self.name}"


class SignalSimulation(models.Model):
    '''
    Description:
        Used to model different BUY/SELL signals.

    Attributes:
        crypto_candle (CryptoCandle): instance of cryptocandle object for which signal is simulated.
        simulation (Simulation): Simulation model being used.
        compare_candle (CryptoCandle): used to calculate signal.
        signal (str): specifies BUY/SELL based on parameters as described in signal.description.
    '''
    crypto_candle = models.ForeignKey(CryptoCandle, on_delete=models.CASCADE, related_name="cryptocandle_simulation")
    simulation = models.ForeignKey(Simulation, on_delete=models.CASCADE)
    candle_compare = models.ForeignKey(CryptoCandle,
                                       null=True,
                                       on_delete=models.SET_NULL,
                                       related_name="cryptocandle_simulation_compare"
                                       )
    signal = models.CharField(max_length=4, null=True)

    def __str__(self):
        return f"{self.crypto_candle} | {self.simulation} | {self.signal}"


class Bank(models.Model):
    '''
    Description:
        Used to model capital fluctuations based on signal.

    Attributes:
        signal_simulation (SignalSimulation): instance of cryptocandle object.
        user (User): instance of user that holds this currency.
        crypto_bank (dec): cryptocurrency amount owned at time of crypto_candle object.
        cash_bank (dec): cash on hand at time of crypto_candle object (currency = crypto_candle.currency_quoted).
    '''
    signal_simulation = models.ForeignKey(SignalSimulation, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # storing values in CharField because Sqlite stores them as float and we do not want to lose decimal point significance.
    crypto_bank = models.CharField(max_length=50, default='0.0')
    cash_bank = models.CharField(max_length=50, default='0.0000')

    def __str__(self):
        return f"{self.signal_simulation} | {self.user} | Crypto Bank: {self.crypto_bank} | Cash Bank: {self.cash_bank}"


class CryptoProphet(models.Model):
    '''
        Description:
            Stores predicted data.

        Attributes:
            date (date): date of prediction
            object_type(str): what is the value we are predicting
            simulation (Simulation): Simulation model being used
            crypto_candle(CryptoCandle): related CryptoCandle if CryptoProphet object is in the past.
            crypto_traded (str): cryptocurrency being tracked
            currency_quoted (str): currency used for the prices
            period_interval (str): Time interval of the candle
            period_close (dec): predicted price in currency_quoted
            trend_ratio (dec): ratio of buy_bitcoin/btc_usd predicted
            update_timestamp (datetime): when record was created in this database

    '''
    date = models.DateField()
    object_type = models.CharField(max_length=50)
    simulation = models.ForeignKey(Simulation, on_delete=models.CASCADE)
    crypto_candle = models.ForeignKey(CryptoCandle, on_delete=models.CASCADE, null=True)
    crypto_traded = models.CharField(max_length=3)
    currency_quoted = models.CharField(max_length=3, default='USD')
    period_interval = models.CharField(max_length=3, default='1d')
    metric_value = models.DecimalField(max_digits=25, decimal_places=10, null=True)
    upper = models.DecimalField(max_digits=25, decimal_places=10, null=True)
    lower = models.DecimalField(max_digits=25, decimal_places=10, null=True)
    change = models.DecimalField(max_digits=25, decimal_places=10, null=True)
    update_timestamp = models.DateTimeField(default=timezone.now())

    def __str__(self):
        return f"{self.object_type} | {self.date} | {self.crypto_traded} | {self.simulation}"
