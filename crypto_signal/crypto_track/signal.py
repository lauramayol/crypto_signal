
from crypto_track.sql_methods import SqlCommands


class Signal():

    def get_latest(self):
        pass

    def get_signal(self, currency, search_date):
        if currency == "" or search_date == "":
            raise TrackException("Please specify a currency in your request.", "Bad Request")

        mydb = SqlCommands('djitter.cmxez4rkpezl.us-east-1.rds.amazonaws.com', 'root', 'crypto_signal')
        filter_statement = f" WHERE currency_traded='{currency}' AND period_start_date='{search_date}'"
        my_signal = mydb.select_results("crypto_track_metrics", filter_statement)
        return_message = {"currency": my_signal[0][0],
                          "currency_quoted": my_signal[0][1],
                          "date": f"{my_signal[0][3]}",
                          "period_close": f"{my_signal[0][4]}",
                          "prior_period_close": f"{my_signal[0][5]}",
                          "signal": f"{my_signal[0][11]}",
                          }

        return return_message
