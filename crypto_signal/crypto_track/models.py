from django.db import models
from django.utils import timezone


class PyTrends(models.Model):
    date = models.DateField(primary_key=True)
    buy_bitcoin = models.IntegerField(null=True)
    btc_usd = models.IntegerField(null=True)
    is_partial = models.BooleanField(default=False)
    trend_ratio = models.DecimalField(max_digits=10, decimal_places=5, null=True)

    def __str__(self):
        return f"{self.date}"


class CryptoCandle(models.Model):
    '''
        crypto_traded (string): cryptocurrency being tracked
        currency_quoted (string): currency used for the prices
        period_interval (string): Time interval of the candle
        period_start_timestamp (string): Start time of the candle in RFC3339
        search_trend (PyTrend): PyTrend object related to that day (can be null)
        period_low (dec): Lowest price in currency_quoted
        period_open(dec): First trade price in currency_quoted
        period_close (dec): Last trade price in currency_quoted
        period_high (dec): Highest price in currency_quoted
        period_volume (dec): Volume transacted in period interval in currency_quoted
        data_source (string): where we got this data
        update_timestamp (datetime): when record was created in this database
        prior_period_candle (CryptoCandle): used to calculate signal
        signal (str): specifies BUY/SELL based on parameters as described in README.md
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
    prior_period_candle = models.ForeignKey('self',
                                            null=True,
                                            on_delete=models.SET_NULL
                                            )
    signal = models.CharField(max_length=4, null=True)

    def __str__(self):
        return f"{self.currency_traded} | {self.period_start_timestamp} | {self.data_source}"


class CryptoTransact(models.Model):
    '''
        crypto_candle (CryptoCandle): which instance of cryptocandle object we are referring to
        crypto_bank (dec): how much cryptocurrency we currently own
        cash_bank (dec): how much cash we have in the bank (in terms of crypto_candle.currency_quoted)
    '''
    crypto_candle = models.ForeignKey(CryptoCandle, on_delete=models.CASCADE)
    crypto_bank = models.DecimalField(max_digits=25, decimal_places=15, null=True)
    cash_bank = models.DecimalField(max_digits=25, decimal_places=15, null=True)
