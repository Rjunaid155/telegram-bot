import requests
import telebot
import os
import pandas as pd
import numpy as np
from datetime import datetime
import time
import ta

# ENV Variables
TELEGRAM_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# RSI Calculation
def calculate_rsi(series, period=14):
    return ta.momentum.RSIIndicator(series, period=period).rsi()

# KDJ Calculation (J value)
def calculate_kdj(df, period=14):
    low_min = df['low'].rolling(period).min()
    high_max = df['high'].rolling(period).max()
    rsv = (df['close'] - low_min) / (high_max - low_min) * 100
    k = rsv.ewm(com=2).mean()
    d = k.ewm(com=2).mean()
    j = 3 * k - 2 * d
    return j

# Fetch all available futures symbols from MEXC
def fetch_symbols():
    url = "https://contract.mexc.com/api/v1/contract/detail"
    response = requests.get(url)
    if response.status_code == 200:
        res_json = response.json()
        symbols = [item['symbol'] for item in res_json['data']]
        return symbols
    else:
        print("Failed to fetch symbol list")
        return []

# Fetch 15m candles
def fetch_candles(symbol, limit=50):
    url = f"https://contract.mexc.com/api/v1/contract/kline/{symbol}?interval=15m&limit={limit}"
    response = requests.get(url)
    if response.status_code == 200:
        res_json = response.json()
        if 'data' not in res_json or not res_json['data']:
            print(f"Skipping {symbol}: No candle data")
            return None
        data = res_json['data']
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df = df.astype({'open': 'float', 'high': 'float', 'low': 'float', 'close': 'float', 'volume': 'float'})
        df = df.iloc[::-1].reset_index(drop=True)
        return df
    else:
        print(f"Skipping {symbol}: {response.text}")
        return None

# Send Telegram Alert
def send_alert(message):
    bot.send_message(CHAT_ID, message)

# Main Signal Function
def check_short_signals():
    pairs = fetch_symbols()  # Get all available pairs

    for symbol in pairs:
        df = fetch_candles(symbol)
        if df is None or len(df) < 20:
            continue

        df['rsi_15m'] = calculate_rsi(df['close'], 14)
        df['j'] = calculate_kdj(df, 14)
        avg_volume = df['volume'].iloc[:-1].mean()
        current_volume = df['volume'].iloc[-1]

        last_rsi = df['rsi_15m'].iloc[-1]
        last_j = df['j'].iloc[-1]
        price = df['close'].iloc[-1]

        if last_rsi > 70 and last_j > 80 and current_volume > 1.5 * avg_volume:
            tp = round(price * 0.995, 4)
            sl = round(price * 1.005, 4)

            message = (
                f"⚠️ [SHORT SIGNAL] {symbol}\n"
                f"📊 Price: {price}\n"
                f"⛔ RSI 15m: {last_rsi:.2f}\n"
                f"⛔ J: {last_j:.2f}\n"
                f"🔥 Volume Spike: {current_volume:.2f} vs Avg {avg_volume:.2f}\n"
                f"✅ Entry: {price}\n"
                f"🎯 Take Profit: {tp}\n"
                f"❌ Stop Loss: {sl}\n"
                f"🕒 Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
            )
            send_alert(message)

# Run forever
if __name__ == "__main__":
    while True:
        check_short_signals()
        time.sleep(300)
