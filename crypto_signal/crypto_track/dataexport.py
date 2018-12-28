import pandas as pd
from crypto_track.models import PyTrends, CryptoCandle, SignalSimulation, Simulation, Bank, CryptoProphet
from django.apps import apps


class DataExport():
    '''
        Load all Django models into flat files. This can be used for many purposes, but initially meant to load Tableau report.

        Attributes:
            Required:
                format (str): format of flat file to export (csv, xls, etc.)
    '''

    model_list = ['PyTrends', 'CryptoCandle', 'SignalSimulation', 'Simulation', 'Bank', 'CryptoProphet']

    def __init__(self, format):
        self.format = format

    def export_csv(self, model_name, app_name='crypto_track'):
        file_name = f"{app_name}_{model_name}.{self.format}"
        # if model_name == 'PyTrends':

        my_model = apps.get_model(app_name, model_name)
        # Handle known NULL exception in CryptoProphet
        # if model_name = 'CryptoProphet':
        # my_model.
        qs = my_model.objects.all().values()
        if model_name == 'CryptoProphet':
            qs.filter(change='NaN').update(change=0)
        print(my_model)
        model_data = list(qs)
        df = pd.DataFrame(model_data)
        if model_name == 'PyTrends':
            index_name = 'date'
        else:
            index_name = 'id'
        df.set_index(index_name, inplace=True)
        # if model_name == 'PyTrends':
        #     df.index = df.date
        # else:
        #     df.index = df.id
        df.to_csv(file_name, quoting=3)
        return f"Successfully saved file {file_name}."

    def export_all(self):
        # Initialize our return variable
        return_message = ""

        for m in self.model_list:
            if self.format == 'csv':
                return_message = return_message + ' ' + self.export_csv(m)

        return return_message
