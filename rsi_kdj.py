import requests
import time
import os
import telebot
import pandas as pd
import pandas_ta as ta
from datetime import datetime

# Telegram setup
TELEGRAM_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Get all UMCBL trading pairs (Futures)
def get_futures_symbols():
    url = "https://api.bitget.com/api/mix/v1/market/contracts?productType=umcbl"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()["data"]
        return [pair["symbol"].replace("_UMCBL", "") for pair in data]
    else:
        print("Failed to fetch symbols:", response.text)
        return []

# Klines fetcher
def get_klines(symbol, interval, limit=100):
    url = f"https://api.bitget.com/api/mix/v1/market/candles?symbol={symbol}_UMCBL&granularity={interval}&limit={limit}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()["data"]
        df = pd.DataFrame(data, columns=[
            "timestamp", "open", "high", "low", "close", "volume", "quoteVol"
        ])
        df = df.iloc[::-1]
        df["close"] = df["close"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        return df
    else:
        print(f"{symbol} failed:", response.text)
        return None

# Indicator check
def check_indicators(symbol, timeframe):
    df = get_klines(symbol, timeframe)
    if df is None or len(df) < 30:
        return

    df.ta.rsi(length=14, append=True)
    df.ta.kdj(append=True)

    latest = df.iloc[-1]
    rsi = latest["RSI_14"]
    j = latest["J_9_3_3"]

    if rsi <= 20 and j <= 10:
        msg = f"🔻 {symbol} ({timeframe}s) OVERSOLD Signal\nRSI: {rsi:.2f}\nKDJ J: {j:.2f}"
        bot.send_message(CHAT_ID, msg)
    elif rsi >= 80 and j >= 90:
        msg = f"🚀 {symbol} ({timeframe}s) OVERBOUGHT Signal\nRSI: {rsi:.2f}\nKDJ J: {j:.2f}"
        bot.send_message(CHAT_ID, msg)

# Main
if __name__ == "__main__":
    symbols = get_futures_symbols()
    timeframes = ["900", "3600"]  # 15m and 1h

    for symbol in symbols:
        for tf in timeframes:
            check_indicators(symbol, tf)
            time.sleep(2)  # Delay to avoid API rate limit
