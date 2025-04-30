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
        return [pair["symbol"].replace("_UMCBL", "") for pair in data if "symbol" in pair]
    else:
        print("Failed to fetch symbols:", response.text)
        return []

# Klines fetcher
def get_klines(symbol, interval, limit=100):
    full_symbol = f"{symbol}_UMCBL"
    url = f"https://api.bitget.com/api/mix/v1/market/candles?symbol={full_symbol}&granularity={interval}&limit={limit}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json().get("data", [])
        if not data:
            print(f"{symbol}: Empty kline data received.")
            return None
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
    rsi = latest.get("RSI_14", None)
    j = latest.get("J_9_3_3", None)

    if rsi is None or j is None:
        print(f"{symbol}: RSI or KDJ J missing.")
        return

    if rsi <= 20 and j <= 10:
        msg = f"🔻 {symbol} ({int(timeframe)//60}m) OVERSOLD Signal\nRSI: {rsi:.2f}\nKDJ J: {j:.2f}"
        bot.send_message(CHAT_ID, msg)
    elif rsi >= 80 and j >= 90:
        msg = f"🚀 {symbol} ({int(timeframe)//60}m) OVERBOUGHT Signal\nRSI: {rsi:.2f}\nKDJ J: {j:.2f}"
        bot.send_message(CHAT_ID, msg)

# Main
if __name__ == "__main__":
    symbols = get_futures_symbols()
    timeframes = ["900", "3600"]  # 15m and 1h

    for symbol in symbols:
        for tf in timeframes:
            try:
                check_indicators(symbol, tf)
                time.sleep(2)
            except Exception as e:
                print(f"Error checking {symbol} ({tf}):", e)
