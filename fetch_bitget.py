import requests
import time
import os
import numpy as np
import pandas as pd
import hmac
import hashlib
import base64
from datetime import datetime, timedelta
from telegram import Bot

# 🔑 Bitget API Keys
API_KEY = os.getenv("BITGET_API_KEY")
SECRET_KEY = os.getenv("BITGET_SECRET_KEY")
PASSPHRASE = os.getenv("BITGET_PASSPHRASE")
TELEGRAM_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

# 📊 Function to fetch order book
def fetch_order_book(market_type, symbol, limit=5):
    if market_type == "spot":
        base_url = "https://api.bitget.com/api/spot/v1/market/depth"
        symbol = f"{symbol}_SPBL"
    elif market_type == "futures":
        base_url = "https://api.bitget.com/api/mix/v1/market/depth"
        if market_type == "futures":
    symbol = f"{symbol.replace('USDT', '')}USDT_UMCBL"  # Ensures correct format
    else:
        return None

    params = {"symbol": symbol, "limit": limit}
    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching {market_type} order book:", response.text)
        return None

# 📈 Fetch price data for indicators
def fetch_klines(symbol, interval):
    base_url = "https://api.bitget.com/api/mix/v1/market/candles"
    valid_intervals = {"1m": "60", "5m": "300", "15m": "900"}  # Correct interval mapping
params = {"symbol": symbol, "granularity": valid_intervals[interval]}
    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        return response.json()["data"]
    else:
        print(f"Error fetching {symbol} {interval} klines:", response.text)
        return None

# 📊 Calculate MA, RSI, MACD
def calculate_indicators(data):
    close_prices = np.array([float(candle[4]) for candle in data])

    ma = np.mean(close_prices[-10:])  
    rsi = 100 - (100 / (1 + np.mean(close_prices[-5:]) / np.mean(close_prices[-10:])))
    macd = close_prices[-1] - np.mean(close_prices[-5:])  

    return ma, rsi, macd

# 🚀 Detect Spike Movements
def detect_spike(data):
    latest_close = float(data[-1][4])
    prev_close = float(data[-2][4])

    spike_threshold = 1.5  
    price_change = ((latest_close - prev_close) / prev_close) * 100

    if abs(price_change) >= spike_threshold:
        return f"⚡ SPIKE ALERT: {price_change:.2f}% Price Movement Detected!"
    return None

# 🔥 Generate SL, TP, Entry, Exit
def generate_trade_levels(entry_price):
    stop_loss = round(entry_price * 0.98, 5)  
    take_profit = round(entry_price * 1.05, 5)  
    exit_price = round(entry_price * 1.03, 5)  

    return stop_loss, take_profit, exit_price

# 🔔 Send alerts to Telegram
def send_telegram_alert(message):
    bot.send_message(CHAT_ID, message)

# 🚀 Fetch & Send Alerts
def check_and_alert():
    symbols = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "SOLUSDT", "ADAUSDT", "DOGEUSDT", "MATICUSDT"]
    timeframes = {"1m": 60, "5m": 300, "15m": 900}

    for symbol in symbols:
        for market in ["spot", "futures"]:
            order_book = fetch_order_book(market, symbol)
            if order_book:
                best_bid = float(order_book["data"]["bids"][0][0])  
                best_ask = float(order_book["data"]["asks"][0][0])  
                entry_price = best_bid  

                stop_loss, take_profit, exit_price = generate_trade_levels(entry_price)
                trend = "📈 Long" if best_bid > best_ask else "📉 Short"

                execution_time = datetime.utcnow() + timedelta(minutes=15)

                message = (
                    f"🔥 {symbol} ({market.upper()}) Trade Signal:\n"
                    f"{trend}\n"
                    f"📌 Entry Price: {entry_price}\n"
                    f"🎯 Take Profit (TP): {take_profit}\n"
                    f"🚪 Exit Price: {exit_price}\n"
                    f"🛑 Stop Loss (SL): {stop_loss}\n"
                    f"⏳ Execution Time: {execution_time.strftime('%H:%M:%S UTC')}"
                )
                send_telegram_alert(message)

            for tf, seconds in timeframes.items():
                klines = fetch_klines(symbol, seconds)
                if klines:
                    ma, rsi, macd = calculate_indicators(klines)
                    spike_alert = detect_spike(klines)

                    signal_msg = (
                        f"📊 {symbol} ({market.upper()}) {tf} Timeframe:\n"
                        f"🔹 MA: {ma:.2f}\n"
                        f"🔸 RSI: {rsi:.2f}\n"
                        f"📊 MACD: {macd:.2f}"
                    )
                    send_telegram_alert(signal_msg)

                    if spike_alert:
                        send_telegram_alert(spike_alert)

# ✅ Run the function
if __name__ == "__main__":
    check_and_alert()
