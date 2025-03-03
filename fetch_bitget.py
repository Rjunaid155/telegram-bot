import requests
import time
import os
import hmac
import hashlib
import base64
import telebot
from datetime import datetime, timedelta

# 🔑 Bitget API Keys (Render ke environment variables se le raha hai)
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
        symbol = f"{symbol}_SPBL"  # ✅ Spot ke liye symbol format
    elif market_type == "futures":
        base_url = "https://api.bitget.com/api/mix/v1/market/depth"
        symbol = f"{symbol}_UMCBL"  # ✅ Futures (USDT-M Perpetual) ke liye symbol format
    else:
        return None

    params = {"symbol": symbol, "limit": limit}
    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching {market_type} order book:", response.text)
        return None

# 🔍 Function to get all trading pairs
def get_all_trading_pairs(market_type):
    if market_type == "spot":
        url = "https://api.bitget.com/api/spot/v1/public/symbols"
    elif market_type == "futures":
        url = "https://api.bitget.com/api/mix/v1/market/contracts?productType=umcbl"
    else:
        return []

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if market_type == "spot":
            return [pair["symbol"].replace("_SPBL", "") for pair in data["data"]]
        else:
            return [pair["symbol"].replace("_UMCBL", "") for pair in data["data"]]
    else:
        print(f"Error fetching {market_type} trading pairs:", response.text)
        return []

# 🔔 Send alerts to Telegram
def send_telegram_alert(message):
    bot.send_message(CHAT_ID, message)

# ⏲️ Get historical data for 15-minute intervals (for predictions)
def get_historical_data(symbol, market):
    if market == "spot":
        base_url = f"https://api.bitget.com/api/spot/v1/market/kline"
        symbol = f"{symbol}_SPBL"
    else:
        base_url = f"https://api.bitget.com/api/mix/v1/market/candles"  # Corrected API endpoint for futures
        symbol = f"{symbol}_UMCBL"

    params = {
        "symbol": symbol,
        "granularity": 900,  # 15-minute candles (900 seconds)
        "limit": 5  # Last 5 candles for trend analysis
    }

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        return response.json()["data"]
    else:
        print(f"Error fetching historical data for {symbol}: {response.text}")
        return None

# ⚡ Predict future movement based on past 15-min data
def predict_movement(symbol, market):
    data = get_historical_data(symbol, market)

    if data:
        # Fetch the last two closing prices
        prev_close = float(data[-2][4])  # Closing price of the previous candle
        current_close = float(data[-1][4])  # Closing price of the current candle

        price_change = ((current_close - prev_close) / prev_close) * 100

        # Long/Short determination based on price movement
        if price_change >= 1.5:  # ✅ Long if price increased by 1.5% or more
            return "LONG", round(price_change, 2)
        elif price_change <= -1.5:  # 🔻 Short if price decreased by 1.5% or more
            return "SHORT", round(price_change, 2)
        else:
            return "HOLD", round(price_change, 2)

    return None, None

# 🚀 Fetch & Send Alerts 15-30 minutes before the prediction
def check_and_alert():
    spot_pairs = get_all_trading_pairs("spot")
    futures_pairs = get_all_trading_pairs("futures")

    for symbol in spot_pairs + futures_pairs:
        market = "spot" if symbol in spot_pairs else "futures"
        signal, change = predict_movement(symbol, market)

        if signal and signal != "HOLD":
            alert_msg = (
                f"🚨 {symbol} ({market.upper()}) Signal Alert:\n"
                f"💼 Position: {signal}\n"
                f"📈 Price Change: {change}%\n"
                f"📅 Prediction Time: {datetime.now() + timedelta(minutes=15)}\n"
                f"Prepare for potential trade in the next 15-30 minutes."
            )
            send_telegram_alert(alert_msg)

# ✅ Run the function
if __name__ == "__main__":
    while True:
        check_and_alert()
        time.sleep(900)  # Check every 15 minutes (900 seconds)
