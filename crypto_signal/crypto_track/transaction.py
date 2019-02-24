from crypto_track.models import CryptoCandle, Bank, SignalSimulation, Simulation
from django.shortcuts import get_object_or_404
import decimal
from django.contrib.auth import get_user_model


class BankTransaction():
    def __init__(self, candle_data, simulation, currency):
        '''
            Attributes (required)
            candle_data (CryptoCandle QuerySet): This is the subset we will use to create bank simulations. This will be useful when creating different Transaction Histories for the same simulations but with different dates and/or users.
            simulation(Simulation): specifies which simulation we are using.

        '''
        self.candle_data = candle_data
        self.simulation = simulation
        self.currency = currency

    def transaction_history(self, trader_name="admin"):
        '''
            Transaction history created for simulation subset. This is separate from self.update_signal because it always needs to go in chronological order whereas update_signal does not.
        '''
        # initialize variables to be used in loop
        # we start with "SELL" because we haven't bought anything yet.
        buy_switch = "SELL"
        trader = get_user_model().objects.get_or_create(username=trader_name)[0]
        prior_sim = None

        # delete if bank object already exists, then re-create.
        Bank.objects.filter(signal_simulation__simulation=self.simulation,
                            user=trader,
                            signal_simulation__crypto_candle__crypto_traded=self.currency
                            ).delete()

        for candle in self.candle_data.order_by('period_start_timestamp'):

            try:
                sim = get_object_or_404(SignalSimulation,
                                        crypto_candle=candle,
                                        simulation=self.simulation)
            except:
                # skip loop if SignalSimulation object is not found.
                next
            else:
                # Initialize our starting cash amount (we know it is beginning because there is no prior_sim.
                if prior_sim is None:

                    my_bank = Bank(signal_simulation=sim,
                                   user=trader,
                                   # crypto_bank=(0.0),
                                   cash_bank='1.0')
                    my_bank.save()
                elif sim.signal:
                    # Remove HOLD signal, make sure it copies signal from prior day
                    if sim.signal == "HOLD":

                        if prior_sim.signal:
                            sim.signal = prior_sim.signal
                        # If we are missing prior signal, then we just assume "SELL" because we haven't bought. Because we are sorting by start date, this will only happen on day 1.
                        else:
                            sim.signal = "SELL"
                        sim.save()
                    # simulate our bank
                    my_bank_results = self.create_transaction(sim, buy_switch, trader, my_bank)
                    my_bank = my_bank_results[0]
                    buy_switch = my_bank_results[1]
                prior_sim = sim
        return my_bank

    def create_transaction(self, my_sim, prior_signal, trader, prior_bank):
        '''
            This is a basic model:
            1. Spend full cash_bank at first BUY signal
            2. Sell full crypto_bank at first SELL signal after a BUY.
        '''

        # If current signal as the same as prior, we do not act, so bank will stay the same.
        if prior_signal != my_sim.signal and my_sim.signal != "HOLD":
            # This means we have cash on hand because prior action was SELL.
            if my_sim.signal == "BUY":
                my_bank = Bank(signal_simulation=my_sim,
                               user=trader,
                               crypto_bank=str(decimal.Decimal(prior_bank.cash_bank) / decimal.Decimal(my_sim.crypto_candle.period_close)),
                               cash_bank=str(0.0))
                buy_switch = "BUY"
            elif my_sim.signal == "SELL":
                my_bank = Bank(signal_simulation=my_sim,
                               user=trader,
                               crypto_bank=str(0.0),
                               cash_bank=str(decimal.Decimal(prior_bank.crypto_bank) * decimal.Decimal(my_sim.crypto_candle.period_close)))
                buy_switch = "SELL"
            my_bank.save()

        else:
            my_bank = prior_bank
            buy_switch = my_sim.signal

        return (my_bank, buy_switch)
