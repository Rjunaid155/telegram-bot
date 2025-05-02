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
    return ta.momentum.RSIIndicator(close=series, window=period).rsi()

# KDJ (J value)
def calculate_kdj(df, period=14):
    low_min = df['low'].rolling(period).min()
    high_max = df['high'].rolling(period).max()
    rsv = (df['close'] - low_min) / (high_max - low_min) * 100
    k = rsv.ewm(com=2).mean()
    d = k.ewm(com=2).mean()
    j = 3 * k - 2 * d
    return j

# Fetch 5m Candles from MEXC
def fetch_candles(symbol, limit=50):
    url = f"https://api.mexc.com/api/v3/klines?symbol={symbol}&interval=5m&limit={limit}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if not data:
            print(f"Skipping {symbol}: No data")
            return None
        # Only 6 columns from API: timestamp, open, high, low, close, volume
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_volume'])
        df = df.astype({'open': 'float', 'high': 'float', 'low': 'float', 'close': 'float', 'volume': 'float'})
        return df
    else:
        print(f"Skipping {symbol}: {response.text}")
        return None
# Send Telegram Alert
def send_alert(message):
    bot.send_message(CHAT_ID, message)

# Signal Check Function
def check_signals():
    pairs = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT']  # apni list daal lena

    for symbol in pairs:
        df = fetch_candles(symbol)
        if df is None or len(df) < 20:
            continue

        df['rsi_5m'] = calculate_rsi(df['close'], 14)
        df['j'] = calculate_kdj(df, 14)
        avg_volume = df['volume'].iloc[:-1].mean()
        current_volume = df['volume'].iloc[-1]

        last_rsi = df['rsi_5m'].iloc[-1]
        last_j = df['j'].iloc[-1]
        price = df['close'].iloc[-1]

        # Conditions
        if last_rsi > 70 and last_j > 80:
            tp = round(price * 0.995, 4)
            sl = round(price * 1.005, 4)
            avoid_price = round(price * 1.002, 4)
            best_entry_low = round(price * 0.998, 4)
            best_entry_high = round(price * 1.000, 4)

            if current_volume > 1.5 * avg_volume:
                signal_type = "🔥 Spike Signal"
            else:
                signal_type = "✅ Normal Signal"

            message = (
                f"{signal_type}\n"
                f"Pair: {symbol}\n"
                f"Price: {price}\n"
                f"RSI (5m): {last_rsi:.2f}\n"
                f"KDJ J (5m): {last_j:.2f}\n"
                f"Volume: {current_volume:.2f} | Avg: {avg_volume:.2f}\n"
                f"Entry Between: {best_entry_low} - {best_entry_high}\n"
                f"❌ Avoid Above: {avoid_price}\n"
                f"TP: {tp} | SL: {sl}\n"
                f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
            )
            send_alert(message)

# Continuous Run
while True:
    check_signals()
    time.sleep(300)
