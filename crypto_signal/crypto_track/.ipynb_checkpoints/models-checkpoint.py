from django.db import models
from datetime import datetime
from django.utils import timezone


class CryptoCandle(models.Model):
    '''
        currency_traded (string): cryptocurrency being tracked
        currency_quoted (string): currency used for the prices
        period_interval (string): Time interval of the candle
        period_start_timestamp (string): Start time of the candle in RFC3339
        period_low (dec): Lowest price in currency_quoted
        period_open(dec): First trade price in currency_quoted
        period_close (dec): Last trade price in currency_quoted
        period_high (dec): Highest price in currency_quoted
        period_volume (dec): Volume transacted in period interval in currency_quoted
        data_source (string): where we got this data
        update_timestamp (datetime): when record was created in this database
    '''
    currency_traded = models.CharField(max_length=3)
    currency_quoted = models.CharField(max_length=3)
    period_interval = models.CharField(max_length=3)
    period_start_timestamp = models.CharField(max_length=50)
    period_low = models.DecimalField(max_digits=25, decimal_places=10)
    period_open = models.DecimalField(max_digits=25, decimal_places=10)
    period_close = models.DecimalField(max_digits=25, decimal_places=10)
    period_high = models.DecimalField(max_digits=25, decimal_places=10)
    period_volume = models.DecimalField(max_digits=25, decimal_places=10)
    data_source = models.CharField(max_length=255)
    update_timestamp = models.DateTimeField(default=timezone.now())

    def __str__(self):
        return f"{self.currency_traded} | {self.period_start_timestamp} | {self.data_source}"


class CryptoCandleHistory(models.Model):
    '''
        currency_traded (string): cryptocurrency being tracked
        currency_quoted (string): currency used for the prices
        period_interval (string): Time interval of the candle
        period_start_timestamp (string): Start time of the candle in RFC3339
        period_low (dec): Lowest price in currency_quoted
        period_open(dec): First trade price in currency_quoted
        period_close (dec): Last trade price in currency_quoted
        period_high (dec): Highest price in currency_quoted
        period_volume (dec): Volume transacted in period interval in currency_quoted
        weighted_price (dec): Volume-weighted average price (VWAP)
        data_source (string): where we got this data
        update_timestamp (datetime): when record was created in this database
    '''
    currency_traded = models.CharField(max_length=3)
    currency_quoted = models.CharField(max_length=3)
    period_interval = models.CharField(max_length=3)
    period_start_timestamp = models.CharField(max_length=50)
    period_low = models.DecimalField(max_digits=25, decimal_places=10)
    period_open = models.DecimalField(max_digits=25, decimal_places=10)
    period_close = models.DecimalField(max_digits=25, decimal_places=10)
    period_high = models.DecimalField(max_digits=25, decimal_places=10)
    period_volume_currency_traded = models.DecimalField(max_digits=25, decimal_places=10)
    period_volume_currency_quoted = models.DecimalField(max_digits=25, decimal_places=10)
    weighted_price = models.DecimalField(max_digits=25, decimal_places=10)
    data_source = models.CharField(max_length=255)
    update_timestamp = models.DateTimeField(default=timezone.now())

    def __str__(self):
        return f"{self.currency_traded} | {self.period_start_timestamp} | {self.data_source}"

class PyTrends(models.Model):
    date = models.DateField(primary_key=True)
    buy_bitcoin = models.IntegerField
    btc_usd = models.IntegerField
    is_partial = models.BooleanField(default = False)
    
    def __str__(self):
        return ""