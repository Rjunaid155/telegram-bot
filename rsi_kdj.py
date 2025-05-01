import requests
import pandas as pd
import telebot
import os
import time
from ta.momentum import RSIIndicator, StochasticOscillator

# Env vars
TELEGRAM_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Get tradable USDT futures pairs
def get_valid_pairs():
    url = "https://api.bitget.com/api/mix/v1/market/contracts?productType=umcbl"
    response = requests.get(url)
    valid_pairs = []
    if response.status_code == 200:
        for pair in response.json()["data"]:
            if pair["quoteCoin"] == "USDT":
                symbol = pair["symbol"].replace("_UMCBL", "")
                if is_pair_valid(symbol):
                    valid_pairs.append(symbol)
    return valid_pairs

# Check if pair has candle data
def is_pair_valid(symbol):
    url = f"https://api.bitget.com/api/mix/v1/market/candles"
    params = {"symbol": f"{symbol}_UMCBL", "granularity": "900", "limit": 2}
    response = requests.get(url, params=params)
    return response.status_code == 200

# Get candles dataframe
def get_candles(symbol, timeframe):
    url = f"https://api.bitget.com/api/mix/v1/market/candles"
    params = {"symbol": f"{symbol}_UMCBL", "granularity": timeframe, "limit": 50}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()["data"]
        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume", "quoteVolume"])
        df = df.astype(float)
        return df[::-1]
    else:
        return None

# Calculate RSI and KDJ
def analyze(symbol):
    df_15m = get_candles(symbol, "900")
    if df_15m is not None:
        rsi = RSIIndicator(df_15m['close'], 14).rsi().iloc[-1]
        kdj = StochasticOscillator(df_15m['high'], df_15m['low'], df_15m['close'], 14)
        j = 3 * kdj.stoch().iloc[-1] - 2 * kdj.stoch_signal().iloc[-1]
        if rsi < 30 and j < 20:
            bot.send_message(CHAT_ID, f"Signal: {symbol}\nRSI: {round(rsi, 2)}\nJ: {round(j, 2)}")

# Run scanner
def run_signals():
    pairs = get_valid_pairs()
    for symbol in pairs:
        analyze(symbol)

# Run loop
while True:
    run_signals()
    time.sleep(300)
