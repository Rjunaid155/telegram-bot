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

# KDJ Calculation (only J)
def calculate_kdj(df, period=14):
    low_min = df['low'].rolling(period).min()
    high_max = df['high'].rolling(period).max()
    rsv = (df['close'] - low_min) / (high_max - low_min) * 100
    k = rsv.ewm(com=2).mean()
    d = k.ewm(com=2).mean()
    j = 3 * k - 2 * d
    return j

# Fetch 15m Candles from MEXC Futures
def fetch_candles(symbol, limit=50):
    url = f"https://contract.mexc.com/api/v1/contract/kline/{symbol}?interval=15m&limit={limit}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json().get('data', [])
        if not data:
            print(f"Skipping {symbol}: No candle data")
            return None
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df = df.astype({'open': 'float', 'high': 'float', 'low': 'float', 'close': 'float', 'volume': 'float'})
        df = df.iloc[::-1].reset_index(drop=True)
        return df
    else:
        print(f"Skipping {symbol}: {response.text}")
        return None

# Fetch all symbols from MEXC Futures
def fetch_symbols():
    url = "https://contract.mexc.com/api/v1/contract/detail"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json().get('data', [])
        return [item['symbol'] for item in data]
    else:
        print("Failed to fetch symbol list")
        return []

# Filter active symbols (with candle data)
def filter_active_symbols(symbols):
    active_symbols = []
    for symbol in symbols:
        url = f"https://contract.mexc.com/api/v1/contract/kline/{symbol}?interval=15m&limit=1"
        response = requests.get(url)
        if response.status_code == 200:
            res_json = response.json()
            if 'data' in res_json and res_json['data']:
                active_symbols.append(symbol)
        time.sleep(0.05)  # prevent hitting rate limit
    return active_symbols

# Send Telegram Alert
def send_alert(message):
    bot.send_message(CHAT_ID, message)

# Main Signal Function
def check_short_signals():
    print("Fetching symbols...")
    pairs = fetch_symbols()
    if not pairs:
        print("No pairs fetched, exiting.")
        return

    print("Filtering active symbols...")
    active_pairs = filter_active_symbols(pairs)
    print(f"Active symbols found: {len(active_pairs)}")

    for symbol in active_pairs:
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

# Continuous Run
if __name__ == "__main__":
    while True:
        check_short_signals()
        time.sleep(300)  # Check every 5 minutes
