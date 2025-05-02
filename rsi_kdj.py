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

def calculate_rsi(series, period=14):
    return ta.momentum.RSIIndicator(series, period=period).rsi()

def calculate_kdj(df, period=14):
    low_min = df['low'].rolling(period).min()
    high_max = df['high'].rolling(period).max()
    rsv = (df['close'] - low_min) / (high_max - low_min) * 100
    k = rsv.ewm(com=2).mean()
    d = k.ewm(com=2).mean()
    j = 3 * k - 2 * d
    return j

def fetch_symbols():
    url = "https://api.mexc.com/api/v3/exchangeInfo"
    response = requests.get(url)
    symbols = []
    if response.status_code == 200:
        data = response.json()
        for s in data['symbols']:
            if s['quoteAsset'] == 'USDT' and s['status'] == 'ENABLED':
                symbols.append(s['symbol'])
    return symbols

def fetch_candles(symbol, limit=50):
    url = f"https://api.mexc.com/api/v3/klines?symbol={symbol}&interval=15m&limit={limit}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if not data:
            print(f"Skipping {symbol}: No candle data")
            return None
        df = pd.DataFrame(data, columns=['timestamp','open','high','low','close','volume','close_time','qav','num_trades','taker_base_vol','taker_quote_vol','ignore'])
        df = df.astype({'open': 'float', 'high': 'float', 'low': 'float', 'close': 'float', 'volume': 'float'})
        return df
    else:
        print(f"Skipping {symbol}: API error")
        return None

def send_alert(message):
    bot.send_message(CHAT_ID, message)

def check_short_signals():
    pairs = fetch_symbols()
    print(f"Checking {len(pairs)} pairs...")

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
            entry_low = round(price * 0.997, 4)
            entry_high = round(price * 1.0025, 4)
            avoid_price = round(price * 1.0035, 4)

            message = (
                f"⚠️ [High Probability SHORT SIGNAL] {symbol}\n"
                f"📊 Price: {price}\n"
                f"⛔ RSI 15m: {last_rsi:.2f}\n"
                f"⛔ J: {last_j:.2f}\n"
                f"🔥 Volume Spike: {current_volume:.2f} vs Avg {avg_volume:.2f}\n"
                f"✅ Best Entry Between: {entry_low} - {entry_high}\n"
                f"❌ Avoid Above: {avoid_price}\n"
                f"🎯 Take Profit: {tp}\n"
                f"❌ Stop Loss: {sl}\n"
                f"🕒 Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
            )
            send_alert(message)

while True:
    check_short_signals()
    time.sleep(300)
