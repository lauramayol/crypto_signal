# Bitcoin Signal
*Release 1.0*

This release provides an API that recommends Buy/Sell of Bitcoin for a given date with intention to maximize profits.

Current version is modeled after Marc Howard's blog: https://hackernoon.com/how-i-created-a-bitcoin-trading-algorithm-with-a-29-return-rate-using-sentiment-analysis-b0db0e777f4

## Features

#### This release
- [x] Get historical transaction data for Bitcoin.
- [x] Get Google Trends data.
- [x] Import data into database.
- [x] Clean/set up views for analysis.
- [x] Identify buy/sell based on parameters described in article.
- [x] Use Django to create API.
- [x] Write api docs and publish.

#### Next release

- [ ] Switch to SQLite database for easier sharing.
- [ ] Use graphical analysis to see how well the current buy/sell recommendations are performing.
- [ ] Explore switching to BitMEX source.
- [ ] Optimize existing parameters (specifically, remove Google Trends parameter and revise BTC price change threshold of $80).
- [ ] Incorporate OHLCV (open, high, low, close,volume) trends.

### Paths

| Location | End Point |
| :-- | :-- |
| Root path | `/`|
| Signal | `/signal`|
| Load Bitcoin data | `/load/nomics`|
| Load trends data | `/load/trends`|

### HTTP request and query methods

| Method | End Point | Query | Description | Examples |
| :-- | :-- | :-- | :-- | :-- |
| `GET` | `/signal` | `?currency=BTC&date=yyyy-mm-dd` | Retrieves the Buy/Sell signal from model in database for given currency (currently only Bitcoin (BTC) available and historical date (Jan 2013-Oct 2018). | `/signal?currency=BTC&date=2018-08-15` |
| `GET` | `/load/nomics` | `?currency=BTC&start=yyyy-mm-dd&end=yyyy-mm-dd` | Full load of candle (OLHCV metrics) from Nomics.com with given currency and start/end dates (optional). Currently defaulted to daily (1d) intervals and start/end is blank (all-time). | `/load/nomics?currency=BTC&start=2018-01-01` |
| `GET` | `/load/trends` | `n/a` | Full load of Google trends Interet Over Time metrics using pytrends library. We are comparing the Google search terms "buy bitcoin" and "BTC USD" Worldwide, and pulling the daily data on 180-day interval starting with today down to 2013.  | `/load/trends` |

### Contribute

- Issue Tracker: https://github.com/lauramayol/crypto_signal/issues
- Source Code: https://github.com/lauramayol/crypto_signal


### Support


If you are having issues, please let me know.



# Project Plan: Bitcoin signal
*Pre-Release*


The goal of this project is to provide an API that recommends Buy/Sell/Hold of Bitcoin at any given time to maximize profitability.

## To-do

### 1.0 release
##### Goal: re-create the example from https://hackernoon.com/how-i-created-a-bitcoin-trading-algorithm-with-a-29-return-rate-using-sentiment-analysis-b0db0e777f4

- [x] Get historical transaction data for Bitcoin.
- [x] Get Google Trends data.
- [x] Import data into database.
- [x] Clean/set up views for analysis.
- [x] Identify buy/sell based on parameters described in article.
- [x] Use Django to create API.
- [x] Write api docs and publish.

### 2.0 release
##### Goal: optimize parameters
- [ ] Switch to SQLite database for easier sharing.
- [ ] Use graphical analysis to see how well the current buy/sell recommendations are performing.
- [ ] Explore switching to BitMEX source.
- [ ] Optimize existing parameters (specifically, remove Google Trends parameter and revise BTC price change threshold of $80).
- [ ] Incorporate OHLCV (open, high, low, close,volume) trends.

### 3.0 release
##### Goal: live model and optimize the data sources
- [ ] What other variables could play a part in Bitcoin price?
- [ ] Get live transactional and order book data.
- [ ] Compare various sources for historical data and implement as needed.




## Contribute

- Issue Tracker: https://github.com/lauramayol/crypto_signal/issues
- Source Code: https://github.com/lauramayol/crypto_signal
