# Project Plan: Bitcoin signal
*Pre-Release*


The goal of this project is to provide an API that recommends Buy/Sell/Hold of Bitcoin at any given time to maximize profitability.

## To-do

### 1.0 release
#### Goal: re-create the example from https://hackernoon.com/how-i-created-a-bitcoin-trading-algorithm-with-a-29-return-rate-using-sentiment-analysis-b0db0e777f4
- [ ] Get historical transaction data for Bitcoin.
- [ ] Get Google Trends data.
- [ ] Import data into database.
- [ ] Clean/set up views for analysis.
- [ ] Identify buy/sell based on parameters described in article.
- [ ] Use Django to create API.
- [ ] Write api docs and publish.

### 2.0 release
#### Goal: live model and optimize the parameters
- [ ] Get live transactional and order book data.
- [ ] Implement live data into current database.
- [ ] Use graphical analysis to see how well the buy/sell recommendations are with existing model.
- [ ] Incorporate OHLCV (open, high, low, close,volume).
- [ ] Regression testing (?) to modify parameters.

### 3.0 release
#### Goal: refine model
- [ ] What other variables could play a part in Bitcoin price?




## Contribute

- Issue Tracker: https://github.com/lauramayol/crypto_signal/issues
- Source Code: https://github.com/lauramayol/crypto_signal
