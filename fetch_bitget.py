import requests
import time
import os
import hmac
import hashlib
import base64
import telebot
import pandas as pd
import numpy as np

# ✅ Environment Variables
API_KEY = os.getenv("BITGET_API_KEY")
SECRET_KEY = os.getenv("BITGET_SECRET_KEY")
PASSPHRASE = os.getenv("BITGET_PASSPHRASE")
TELEGRAM_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ✅ Signature Generation
def generate_signature(timestamp, method, request_path, body=""):
    message = f"{timestamp}{method}{request_path}{body}"
    signature = hmac.new(SECRET_KEY.encode(), message.encode(), hashlib.sha256).digest()
    return base64.b64encode(signature).decode()

# ✅ Fetch Kline (candlestick) data
def fetch_klines(symbol, interval="15min", limit=100):
    url = "https://api.bitget.com/api/mix/v1/market/candles"
    params = {
        "symbol": f"{symbol}_UMCBL",
        "granularity": interval,
        "limit": limit
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()["data"]
    else:
        print("Error fetching klines:", response.text)
        return None

# ✅ Calculate RSI
def calculate_rsi(prices, period=14):
    delta = np.diff(prices)
    gains = np.maximum(delta, 0)
    losses = np.abs(np.minimum(delta, 0))
    
    avg_gain = np.convolve(gains, np.ones(period)/period, mode='valid')
    avg_loss = np.convolve(losses, np.ones(period)/period, mode='valid')
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi[-1] if len(rsi) > 0 else None

# ✅ Calculate Moving Average (MA)
def calculate_ma(prices, period=14):
    ma = pd.Series(prices).rolling(window=period).mean()
    return ma.iloc[-1]

# ✅ Calculate MACD
def calculate_macd(prices, short_period=12, long_period=26, signal_period=9):
    short_ema = pd.Series(prices).ewm(span=short_period).mean()
    long_ema = pd.Series(prices).ewm(span=long_period).mean()
    macd = short_ema - long_ema
    signal_line = macd.ewm(span=signal_period).mean()
    return macd.iloc[-1], signal_line.iloc[-1]

# ✅ Send Telegram Alert
def send_telegram_alert(message):
    bot.send_message(CHAT_ID, message)

# ✅ Generate Trade Signal
def generate_signals(symbol):
    klines = fetch_klines(symbol)
    if not klines:
        return

    prices = [float(candle[4]) for candle in klines]  # Closing prices
    current_price = prices[-1]

    rsi = calculate_rsi(prices)
    ma = calculate_ma(prices)
    macd, signal_line = calculate_macd(prices)

    if rsi and ma and macd and signal_line:
        if rsi < 30 and macd > signal_line and current_price > ma:  # ✅ Strong Buy Signal
            entry = round(current_price, 4)
            sl = round(entry * 0.98, 4)
            tp = round(entry * 1.02, 4)
            message = (f"🚀 Strong Buy Signal Detected\n"
                       f"📈 Symbol: {symbol}\n"
                       f"💲 Entry Price: {entry}\n"
                       f"🔻 Stop Loss: {sl}\n"
                       f"🔺 Take Profit: {tp}\n"
                       f"📊 RSI: {round(rsi, 2)}\n"
                       f"📈 MACD: {round(macd, 2)}\n")
            send_telegram_alert(message)

        elif rsi > 70 and macd < signal_line and current_price < ma:  # ✅ Strong Sell Signal
            entry = round(current_price, 4)
            sl = round(entry * 1.02, 4)
            tp = round(entry * 0.98, 4)
            message = (f"⚠️ Strong Sell Signal Detected\n"
                       f"📉 Symbol: {symbol}\n"
                       f"💲 Entry Price: {entry}\n"
                       f"🔻 Stop Loss: {sl}\n"
                       f"🔺 Take Profit: {tp}\n"
                       f"📊 RSI: {round(rsi, 2)}\n"
                       f"📈 MACD: {round(macd, 2)}\n")
            send_telegram_alert(message)

# ✅ Main Function (15-min checks)
def main():
    symbols = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "DOGEUSDT"]  # Aap yahan apne favourite pairs add kar sakte hain
    while True:
        for symbol in symbols:
            generate_signals(symbol)
        time.sleep(900)  # 15-minute interval (900 seconds)

if __name__ == "__main__":
    main()
