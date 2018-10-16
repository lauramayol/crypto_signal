from django.shortcuts import render
import urllib.request
import os
from django.utils import timezone
from crypto_track.models import CryptoCandle


class NomicsApp:

    api_key = os.environ["NOMICS_API_KEY"]

    def load_candle(request):
        update_ts = timezone.now()
        candle_url = "https://api.nomics.com/v1/candles"
        period_interval = "1d"
        currency_quote = "USD"

        try:
            query_currency = request.POST.get('currency', '')
        except:
            return JsonResponse({"status_code": 400, "status": "Bad Request",
                                 "message": "Please submit a valid request."})
        else:
            api_url = f"{candle_url}?key={self.api_key}&interval={period_interval}&currency={query_currency}"

            # Get start and end dates if provided
            final_url = append_optional_params("start", api_url)
            final_url = append_optional_params("end", final_url)

            # Read API
            historical_crypto_results = urllib.request.urlopen(final_url).read()

            data_source = f"Nomics {candle_url}"

            for record in historical_crypto_results:
                db_record = CryptoCandle(currency_traded=query_currency, currency_quoted=currency_quote, period_interval=period_interval, period_start_timestamp=record['timestamp'], period_low=record['low'], period_open=record['open'], period_close=record['close'], period_high=record['high'], period_volume=record['volume'], data_source=data_source, update_timestamp=update_ts
                                         )
                db_record.save()
            record_num = historical_crypto_results.count()
            return f"Inserted {record_num} records on {update_ts}."

    def append_optional_params(request, var_name, url_og):
        var_value = request.POST.get(var_name, '')

        if var_value:
            url_og += f"&{var_name}={var_value}"

        return url_og
