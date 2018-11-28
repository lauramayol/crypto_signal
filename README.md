# Bitcoin Signal
*Release 1.1*

The goal of this project is to provide an API that recommends Buy/Sell/Hold of Bitcoin at any given time to maximize profitability.


## Features

#### This release
- [x] Switch to SQLite database for easier sharing.
- [x] Use [graphical analysis](https://public.tableau.com/profile/laura.mayol.vargas#!/vizhome/CryptoSignal1_0/BitcoinBUYSELLmodel) to see how well the current buy/sell recommendations are performing.
- [x] Released Hindisght simulation (best case scenario).
    - BUY: When next day close price increases.
    - SELL: When next day close price decreases.
- [x] Released Version 1.1 simulation (modified price parameter).
    - BUY:
        1. BTC price closes more than 1% above the prior day’s close price.
        2. Search terms of “Buy Bitcoin” to “BTC USD” ratio is higher than 35% (Google Trends).
    - SELL: When price and ratio do not meet BUY requirements.
- [x] Home page created at root path that lists the simulations available and links to visualization.

#### Next release
- [ ] Incorporate OHLCV (open, high, low, close,volume) trends with ML algorithm.

## Running project locally

0. You'll need **Python 3.6 or later** for running the project. Check your version with
```
python3 --version
```
1. Clone repo to your development environment
```
git clone https://github.com/lauramayol/crypto_signal.git
```
2. Install [virtualenv](https://virtualenv.pypa.io/en/latest/)
```
pip install virtualenv
```
3. Change directory to project folder
```
cd crypto_signal
```
4. Start virtualenv
```
virtualenv --python=/usr/local/bin/python3 env
```
5. Run virtualenv
```
source env/bin/activate
```
6. Install dependencies using [pip](https://pip.pypa.io/en/latest/installing.html)
```
pip3 install -r requirements.txt
```
7. Add Nomics Api Key to environment variables. [Nomics](https://nomics.com/)
```
export NOMICS_API_KEY=YOUR_API_KEY
```
8. Run development server
```
python crypto_signal/manage.py runserver
```
9. Check <http://127.0.0.1:8000/> on your browser.


### Endpoints

| Location | Endpoint |
| :-- | :-- |
| Root path | `/`|
| Signal | `/<simulation_id>/signal`|
| Load Bitcoin data | `/load/nomics`|
| Load trends data | `/load/trends`|
| Update candles foreign keys | `/update/candles`|
| Update BUY/SELL signal | `/update/<simulation_id>/signal`|


### HTTP request and query methods

| Method | Endpoint | Query | Description | Examples |
| :-- | :-- | :-- | :-- | :-- |
| `GET` | `/` | `n/a` | Retrieves the current list of Simulations that can generate a signal. Reference this list to use the correct simulation_id with other methods. | `/` |
| `GET` | `/<simulation_id>/signal` | `?currency=BTC&date=yyyy-mm-dd` | Retrieves the Buy/Sell signal from specified simulation in database for given currency (currently only Bitcoin (BTC) available and historical date (Jan 2013-Oct 2018). | `/1/signal?currency=BTC&date=2018-08-15` |
| `POST` | `/load/nomics` | `?currency=BTC&start=yyyy-mm-dd&end=yyyy-mm-dd` | Full load of candle (OLHCV metrics) from Nomics.com with given currency and start/end dates (optional). Currently defaulted to daily (1d) intervals and start/end is blank (all-time). | `/load/nomics?currency=BTC&start=2018-01-01` |
| `POST` | `/load/trends` | `?currency=BTC` | Full load of Google trends Interest Over Time metrics using pytrends library. We are comparing the Google search terms "buy bitcoin" and "BTC USD" Worldwide, and pulling the daily data on 180-day interval starting with today down to 2013.  | `/load/trends?currency=BTC` |
| `PATCH` | `/update/candles` | `?currency=BTC` | Updates foreign key relationship of candle to trend model.  | `/update/candles?currency=BTC` |
| `PATCH` | `/update/<simulation_id>/signal` | `?currency=BTC` | Updates BUY/SELL signal for each candle based on specified simulation.  | `/update/1/signal?currency=BTC` |

### Contribute

- Issue Tracker: https://github.com/lauramayol/crypto_signal/issues
- Source Code: https://github.com/lauramayol/crypto_signal


### Support


If you are having issues, please let me know by posting on Issue Tracker.



# Project Plan: Bitcoin signal
*Pre-Release*


The goal of this project is to provide an API that recommends Buy/Sell/Hold of Bitcoin at any given time to maximize profitability.

## To-do

### 1.0 release
##### Goal: re-create the example from [Marc Howard's blog](https://hackernoon.com/how-i-created-a-bitcoin-trading-algorithm-with-a-29-return-rate-using-sentiment-analysis-b0db0e777f4)

    BUY Signal:
    1. BTC price difference closes more than $80 above the prior day’s close price.
    2. Search terms of “Buy Bitcoin” to “BTC USD” ratio is higher than 35% (Google Trends).
    SELL Signal:
    When price and ratio do not meet BUY requirements.


- [x] Get historical transaction data for Bitcoin.
- [x] Get Google Trends data.
- [x] Import data into database.
- [x] Identify buy/sell based on parameters described in blog.
- [x] Use Django to create API.
- [x] Write api docs and publish.

### 1.1 release
##### Goal: socialize model
- [x] Switch to SQLite database for easier sharing.
- [x] Use [graphical analysis](https://public.tableau.com/profile/laura.mayol.vargas#!/vizhome/CryptoSignal1_0/BitcoinBUYSELLmodel) to see how well the current buy/sell recommendations are performing.
- [x] Released Hindisght simulation (best case scenario).
- [x] Home page created at root path that lists the simulations available and links to visualization.

### 2.0 release
##### Goal: Incorporate ML
- [ ] Incorporate OHLCV (open, high, low, close,volume) trends with ML algorithm.

### 3.0 release
##### Goal: Optimize the data sources
- [ ] Explore other sources (ie. BitMEX, CCXT).
- [ ] Optimize existing parameters as needed (specifically, revise Google Trends and BTC price change thresholds).
- [ ] What other variables could play a part in Bitcoin price?

### 4.0 release
##### Goal: Live model
- [ ] Get live transactional and order book data.
- [ ] Schedule regular data refreshes on live server.




## Contribute

- Issue Tracker: https://github.com/lauramayol/crypto_signal/issues
- Source Code: https://github.com/lauramayol/crypto_signal
