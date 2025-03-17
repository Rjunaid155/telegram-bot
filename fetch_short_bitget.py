import requests
import os
import hmac
import hashlib
import base64
import telebot
import pandas_ta as ta
import pandas as pd
from datetime import datetime, timedelta

# 🔑 Bitget API Keys (from environment variables)
API_KEY = os.getenv("BITGET_API_KEY")
SECRET_KEY = os.getenv("BITGET_SECRET_KEY")
PASSPHRASE = os.getenv("BITGET_PASSPHRASE")
TELEGRAM_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# 🛠️ Signature generation function (v2)
def generate_signature(timestamp, method, request_path, body=""):
    message = f"{timestamp}{method}{request_path}{body}"
    signature = hmac.new(SECRET_KEY.encode(), message.encode(), hashlib.sha256).digest()
    return base64.b64encode(signature).decode()

# 📊 Fetch order book (Spot & Futures)
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

# 🔍 Get all trading pairs
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

# 📅 Get alert time (5 minutes before trade)
def get_alert_time():
    return (datetime.utcnow() + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')

# 🔔 Send alerts to Telegram
def send_telegram_alert(message):
    bot.send_message(CHAT_ID, message)

# 📈 Calculate RSI, EMA, MACD, Bollinger Bands using pandas_ta
def calculate_indicators(data):
    df = pd.DataFrame(data, columns=['price'])
    df['RSI'] = ta.rsi(df['price'], length=14)  # RSI
    df['EMA'] = ta.ema(df['price'], length=9)  # EMA
    df['MACD'] = ta.macd(df['price'], fast=12, slow=26, signal=9)['MACD_12_26_9']  # MACD
    df['BB_upper'], df['BB_middle'], df['BB_lower'] = ta.bbands(df['price'], length=20)  # Bollinger Bands
    return df

# 🏦 Fetch on-chain data from Mempool
def fetch_mempool_data():
    response = requests.get("https://mempool.space/api/mempool")
    if response.status_code == 200:
        return response.json()
    else:
        print("Error fetching Mempool data:", response.text)
        return None

# 🚀 Check and send SHORT trade signals with indicators and Mempool data
def check_and_alert_short():
    spot_pairs = get_all_trading_pairs("spot")
    futures_pairs = get_all_trading_pairs("futures")
    previous_prices = {}

    for symbol in spot_pairs + futures_pairs:
        market = "spot" if symbol in spot_pairs else "futures"
        data = fetch_order_book(market, symbol)

        if data:
            best_bid = float(data["data"]["bids"][0][0])
            stop_loss = round(best_bid * 1.005, 4)
            take_profit = round(best_bid * 0.995, 4)

            # 📈 Calculate indicators
            indicators = calculate_indicators([best_bid])

            # 🏦 Fetch Mempool data
            mempool_data = fetch_mempool_data()

            alert_msg = (
                f"⚡ {symbol} ({market.upper()}) 5-Minute SHORT Trade Signal:\n"
                f"⏰ Alert for: {get_alert_time()} (5 minutes early)\n"
                f"📌 Entry Price: {best_bid}\n"
                f"📉 Stop Loss: {stop_loss}\n"
                f"📈 Take Profit: {take_profit}\n\n"
                f"📊 Indicators:\n"
                f"RSI: {indicators['RSI'].iloc[-1]}\n"
                f"EMA: {indicators['EMA'].iloc[-1]}\n"
                f"MACD: {indicators['MACD'].iloc[-1]}\n"
                f"Bollinger Bands: {indicators['BB_upper'].iloc[-1]} (Upper), {indicators['BB_middle'].iloc[-1]} (Middle), {indicators['BB_lower'].iloc[-1]} (Lower)\n\n"
                f"🏦 On-Chain (Mempool): {mempool_data['count']} unconfirmed transactions"
            )
            send_telegram_alert(alert_msg)

# ✅ Run the function for SHORT trades
if __name__ == "__main__":
    check_and_alert_short()
