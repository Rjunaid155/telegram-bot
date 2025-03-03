import requests
import time
import os
import hmac
import hashlib
import base64
import telebot
import pandas as pd
import numpy as np

# 🔐 API Keys (Render ke environment variables se)
API_KEY = os.getenv("BITGET_API_KEY")
SECRET_KEY = os.getenv("BITGET_SECRET_KEY")
PASSPHRASE = os.getenv("BITGET_PASSPHRASE")
TELEGRAM_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# 📊 Signature generation
def generate_signature(timestamp, method, request_path, body=""):
    message = f"{timestamp}{method}{request_path}{body}"
    signature = hmac.new(SECRET_KEY.encode(), message.encode(), hashlib.sha256).digest()
    return base64.b64encode(signature).decode()

# 📈 Fetch historical data for indicators (corrected params)
def fetch_candles(symbol, interval="15min", limit=100):
    url = "https://api.bitget.com/api/mix/v1/market/candles"
    params = {"symbol": symbol, "granularity": interval, "limit": str(limit)}
    headers = {
        "Content-Type": "application/json",
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": generate_signature(str(int(time.time() * 1000)), "GET", "/api/mix/v1/market/candles"),
        "ACCESS-TIMESTAMP": str(int(time.time() * 1000)),
        "ACCESS-PASSPHRASE": PASSPHRASE
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200 and "data" in response.json():
        return response.json()["data"]
    else:
        print(f"Error fetching candles for {symbol}: {response.text}")
        return None

# 📊 Calculate RSI
def calculate_rsi(prices, period=14):
    delta = np.diff(prices)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)

    avg_gain = np.mean(gain[:period])
    avg_loss = np.mean(loss[:period])

    rsis = []
    for i in range(period, len(prices)):
        avg_gain = (avg_gain * (period - 1) + gain[i - 1]) / period
        avg_loss = (avg_loss * (period - 1) + loss[i - 1]) / period
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        rsi = 100 - (100 / (1 + rs))
        rsis.append(rsi)

    return rsis[-1]

# 📈 Moving Average (MA)
def calculate_ma(prices, period=50):
    return np.mean(prices[-period:])

# 📉 MACD Calculation
def calculate_macd(prices, short=12, long=26, signal=9):
    short_ema = pd.Series(prices).ewm(span=short).mean()
    long_ema = pd.Series(prices).ewm(span=long).mean()
    macd = short_ema - long_ema
    signal_line = macd.ewm(span=signal).mean()
    return macd.iloc[-1], signal_line.iloc[-1]

# 📊 Fetch order book data
def fetch_order_book(symbol, limit=5):
    url = "https://api.bitget.com/api/mix/v1/market/depth"
    params = {"symbol": symbol, "limit": limit}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()["data"]
        best_bid = float(data["bids"][0][0])
        best_ask = float(data["asks"][0][0])
        return best_bid, best_ask
    else:
        print(f"Error fetching order book for {symbol}: {response.text}")
        return None, None

# 🔥 Short trade signal detection
def detect_short_trade(symbol):
    candles = fetch_candles(symbol)
    if not candles:
        return

    prices = [float(candle[4]) for candle in candles]  # Close prices

    rsi = calculate_rsi(prices)
    ma = calculate_ma(prices)
    macd, signal = calculate_macd(prices)
    best_bid, _ = fetch_order_book(symbol)

    # 📉 Bearish conditions for SHORT trade
    if rsi > 70 and macd < signal and prices[-1] < ma:
        sl = round(best_bid * 1.02, 4)  # Stop Loss 2% above entry
        tp = round(best_bid * 0.98, 4)  # Take Profit 2% below entry
        alert_msg = (
            f"⚡ Strong Short Trade Signal ⚡\n"
            f"📉 Coin: {symbol}\n"
            f"📊 RSI: {round(rsi, 2)}\n"
            f"📈 MA: {round(ma, 2)}\n"
            f"📉 MACD: {round(macd, 2)} | Signal: {round(signal, 2)}\n"
            f"💸 Entry Price: {best_bid}\n"
            f"📉 Stop Loss: {sl}\n"
            f"📈 Take Profit: {tp}\n"
            f"🕒 Prediction: Next 15 min!"
        )
        send_telegram_alert(alert_msg)

# 📲 Send message to Telegram
def send_telegram_alert(message):
    bot.send_message(CHAT_ID, message, parse_mode="Markdown")

# 🚀 Monitor all altcoins
def monitor_all_coins():
    url = "https://api.bitget.com/api/mix/v1/market/contracts?productType=umcbl"
    response = requests.get(url)
    if response.status_code == 200:
        coins = [pair["symbol"] for pair in response.json()["data"]]
        print(f"✅ Monitoring these coins: {coins}")
        for coin in coins:
            detect_short_trade(coin)
    else:
        print("Error fetching coins:", response.text)

# ✅ Main loop (5 min interval)
if __name__ == "__main__":
    while True:
        print("🚀 Checking for short trade signals...")
        monitor_all_coins()
        time.sleep(300)  # 5 minutes interval
