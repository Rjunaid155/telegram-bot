import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import time

# Telegram Bot config (from environment variables)
TELEGRAM_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# MEXC Futures API endpoint
BASE_URL = "https://contract.mexc.com/api/v1/contract/kline"

# List of symbols to scan (you can dynamically fetch all too)
symbols = ['BTC_USDT', 'ETH_USDT', 'XRP_USDT']  # Add/remove as needed

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    requests.post(url, data=payload)

def get_klines(symbol, interval="5m", limit=20):
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        return response.json()['data']
    return []

def calculate_rsi(close_prices, period=14):
    delta = np.diff(close_prices)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)

    avg_gain = np.convolve(gain, np.ones(period), 'valid') / period
    avg_loss = np.convolve(loss, np.ones(period), 'valid') / period

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return np.concatenate((np.full(period, np.nan), rsi))

def check_short_signal(candle, rsi_value):
    open_price = float(candle['open'])
    high_price = float(candle['high'])
    close_price = float(candle['close'])

    upper_wick = (high_price - max(open_price, close_price)) / close_price * 100

    if rsi_value >= 75 and 0.5 <= upper_wick <= 1.5:
        return True, upper_wick
    return False, upper_wick

def run_scanner():
    for symbol in symbols:
        klines = get_klines(symbol)
        if len(klines) < 15:
            continue

        close_prices = [float(k['close']) for k in klines]
        rsi_values = calculate_rsi(close_prices)

        last_rsi = rsi_values[-1]
        last_candle = klines[-2]  # last completed candle

        signal, wick_size = check_short_signal(last_candle, last_rsi)
        if signal:
            message = (f"🔴 SHORT Signal Alert!\n"
                       f"Symbol: {symbol}\n"
                       f"RSI: {last_rsi:.2f}\n"
                       f"Upper Wick: {wick_size:.2f}%\n"
                       f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
            send_telegram_message(message)

# Run the scanner loop every 5 mins
while True:
    run_scanner()
    time.sleep(300)
