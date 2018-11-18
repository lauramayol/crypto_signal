import ccxt

with open('api.txt', 'r') as f:
	api = f.readlines()
	apiKey = api[0][:len(api[0])-1]
	secret = api[1][:len(api[1])]

# NOTE: If you are using a different exchange than binance, modify the line below
exchange = ccxt.binance({
	'options': {'adjustForTimeDifference': True},
	'apiKey': apiKey,
	'secret': secret})

def coin_price(coin):
	'''Returns the current dollar price of the coin in question'''
	btc_price = float(exchange.fetch_ticker('BTC/USDT')['info']['lastPrice'])
	if coin == 'BTC':
		return btc_price
	else:
		btc_ratio = float(exchange.fetch_ticker(coin + '/BTC')['info']['lastPrice'])
		return btc_ratio * btc_price

def determine_ticker(coin1, coin2):
	'''Determines if there is an existing ratio for two coins'''
	try:
		exchange.fetch_ticker(coin1 + '/' + coin2)
		return True
	except:
		try:
			exchange.fetch_ticker(coin2 + '/' + coin1)
			return True
		except:
			return
