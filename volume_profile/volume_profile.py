import ccxt
import pandas as pd
import matplotlib.pyplot as plt

exchange = ccxt.binance({
    'options': {
        'defaultType': 'future',
        'enableRateLimit': True,
    },
})

symbol = 'BTC/USDT'

candles = exchange.fetch_ohlcv(symbol, timeframe = '1m', limit =1000)
candles = pd.DataFrame(candles, columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume'])
print(len(candles))

profile = range(int(candles['Low'].min()), int(candles['High'].max()))
profile = { price: 0 for price in profile }
for candle in candles.itertuples(index=False):
    profile.update({
        price: volume + candle.Volume for price, volume in profile.items()
        if price >= candle.Low and price < candle.High
    })

plt.bar(*zip(*profile.items()))
plt.show()