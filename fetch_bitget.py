import requests
import time
import datetime
import pandas as pd
import numpy as np
from telegram import Bot

# Telegram bot setup
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Bitget API endpoint
BITGET_API_URL = "https://api.bitget.com/api/mix/v1/market/candles"

# Mempool API for Bitcoin data
MEMPOOL_API_URL = "https://mempool.space/api/mempool"

# Fetch candles from Bitget
def fetch_candles(symbol, granularity="300", limit="100"):
    end_time = int(time.time() * 1000)
    start_time = end_time - (3600000)  # last 1 hour
    params = {
        "symbol": symbol,
        "granularity": granularity,
        "limit": limit,
        "startTime": start_time,
        "endTime": end_time,
    }
    try:
        response = requests.get(BITGET_API_URL, params=params)
        data = response.json().get("data", [])
        return pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume", "value"])
    except Exception as e:
        print("Error fetching candles:", e)
        return pd.DataFrame()

# Calculate RSI
def calculate_rsi(df, period=14):
    df["close"] = pd.to_numeric(df["close"])
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df

# Calculate MACD
def calculate_macd(df, short=12, long=26, signal=9):
    df["EMA12"] = df["close"].ewm(span=short, adjust=False).mean()
    df["EMA26"] = df["close"].ewm(span=long, adjust=False).mean()
    df["MACD"] = df["EMA12"] - df["EMA26"]
    df["Signal"] = df["MACD"].ewm(span=signal, adjust=False).mean()
    return df

# Moving Average (MA)
def calculate_ma(df, period=50):
    df["MA50"] = df["close"].rolling(window=period).mean()
    return df

# Fetch mempool data
def fetch_mempool_data():
    try:
        response = requests.get(MEMPOOL_API_URL)
        return response.json()
    except Exception as e:
        print("Error fetching mempool data:", e)
        return {}

# Send trade signals to Telegram
def send_telegram_message(message):
    bot.send_message(chat_id=CHAT_ID, text=message)

# Detect short trades
def detect_short_trade(df, symbol):
    if df.iloc[-1]["RSI"] > 70 and df.iloc[-1]["MACD"] < df.iloc[-1]["Signal"] and df.iloc[-1]["close"] < df.iloc[-1]["MA50"]:
        entry_price = df.iloc[-1]["close"]
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"🔴 Short Signal: {symbol}\nEntry Price: {entry_price}\nTime: {now}"
        print(message)
        send_telegram_message(message)

# Monitor all coins
def monitor_all_coins():
    symbols = ["BTCUSDT_UMCBL", "ETHUSDT_UMCBL", "SOLUSDT_UMCBL"]  # Add more coins if needed
    while True:
        for symbol in symbols:
            print(f"🚀 Checking {symbol} for short trade signals...")
            candles = fetch_candles(symbol)
            if not candles.empty:
                candles = calculate_rsi(candles)
                candles = calculate_macd(candles)
                candles = calculate_ma(candles)
                detect_short_trade(candles, symbol)
        time.sleep(180)  # Check every 3 minutes

if __name__ == "__main__":
    monitor_all_coins()
