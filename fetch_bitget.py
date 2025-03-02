import requests
import time
import os
import hmac
import hashlib
import base64
import telebot

# 🔑 Bitget API Keys (Render Environment Variables se le raha hai)
API_KEY = os.getenv("BITGET_API_KEY")
SECRET_KEY = os.getenv("BITGET_SECRET_KEY")
PASSPHRASE = os.getenv("BITGET_PASSPHRASE")  # Futures trading ke liye zaroori hai
TELEGRAM_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# 🛠️ Signature generation function
def generate_signature(timestamp, method, request_path, body=""):
    message = f"{timestamp}{method}{request_path}{body}"
    signature = hmac.new(SECRET_KEY.encode(), message.encode(), hashlib.sha256).digest()
    return base64.b64encode(signature).decode()

# 📊 Function to fetch order book (Spot & Futures)
def fetch_order_book(market_type, symbol, limit=5):
    if market_type == "spot":
        base_url = "https://api.bitget.com/api/spot/v1/market/depth"
        symbol = f"{symbol}_SPBL"  
    elif market_type == "futures":
        base_url = "https://api.bitget.com/api/mix/v1/market/depth"
        symbol = f"{symbol}_UMCBL"  
    else:
        return None

    params = {"symbol": symbol, "limit": limit}
    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching {market_type} order book:", response.text)
        return None

# 📈 Function to fetch historical price data for RSI, MACD, MA
def fetch_klines(symbol, interval):
    base_url = "https://api.bitget.com/api/mix/v1/market/candles"
    params = {"symbol": symbol, "granularity": interval}
    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        return response.json()["data"]
    else:
        print(f"Error fetching {symbol} {interval} klines:", response.text)
        return None

# 📊 Technical Analysis: Moving Average, RSI, MACD
def calculate_indicators(data):
    close_prices = [float(candle[4]) for candle in data] 

    ma = sum(close_prices[-10:]) / 10  # 10-period Moving Average
    rsi = sum(close_prices[-5:]) / sum(close_prices[-10:]) * 100  # Simplified RSI
    macd = close_prices[-1] - sum(close_prices[-5:]) / 5  # MACD (Fast - Slow EMA)

    return ma, rsi, macd

# 📌 Spike Trading Alert
def detect_spike(data):
    latest_close = float(data[-1][4])
    prev_close = float(data[-2][4])

    spike_threshold = 1.5  # 1.5% sudden move
    price_change = ((latest_close - prev_close) / prev_close) * 100

    if abs(price_change) >= spike_threshold:
        return "🔴 SPIKE ALERT: Sudden Price Movement Detected!"
    return None

# 🔔 Send alerts to Telegram
def send_telegram_alert(message):
    bot.send_message(CHAT_ID, message)

# 🚀 Fetch & Send Alerts
def check_and_alert():
    symbols = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "SOLUSDT", "ADAUSDT"]  # Auto-fetch Altcoins
    timeframes = {"1m": 60, "5m": 300, "15m": 900}  

    for symbol in symbols:
        for market in ["spot", "futures"]:
            order_book = fetch_order_book(market, symbol)
            if order_book:
                best_bid = float(order_book["data"]["bids"][0][0])  
                best_ask = float(order_book["data"]["asks"][0][0])  

                trend = "📈 Long" if best_bid > best_ask else "📉 Short"
                message = f"🔥 {symbol} ({market.upper()}) Signal:\n{trend}\nBest Bid: {best_bid}\nBest Ask: {best_ask}"
                send_telegram_alert(message)

            for tf, seconds in timeframes.items():
                klines = fetch_klines(symbol, seconds)
                if klines:
                    ma, rsi, macd = calculate_indicators(klines)
                    spike_alert = detect_spike(klines)

                    signal_msg = f"📊 {symbol} ({market.upper()}) {tf} Signal:\nMA: {ma:.2f}\nRSI: {rsi:.2f}\nMACD: {macd:.2f}"
                    send_telegram_alert(signal_msg)

                    if spike_alert:
                        send_telegram_alert(spike_alert)

# ✅ Run the function
if __name__ == "__main__":
    check_and_alert()
