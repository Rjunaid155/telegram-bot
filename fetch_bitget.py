import requests
import time
import os
import numpy as np
from datetime import datetime, timedelta
from telegram import Bot

# 🔑 Bitget API Keys
API_KEY = os.getenv("BITGET_API_KEY")
SECRET_KEY = os.getenv("BITGET_SECRET_KEY")
PASSPHRASE = os.getenv("BITGET_PASSPHRASE")
TELEGRAM_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

# 📌 Function to get all available altcoins (correct URL and parameters)
def fetch_all_altcoins():
    url = "https://api.bitget.com/api/mix/v1/market/contracts?productType=umcbl"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()["data"]
        altcoins = [coin["symbol"].replace("_UMCBL", "") for coin in data if "USDT" in coin["symbol"]]
        return altcoins
    else:
        print("Error fetching altcoins:", response.text)
        return []

# 📊 Function to fetch order book with correct params
def fetch_order_book(market_type, symbol, limit=5):
    base_url = "https://api.bitget.com/api/mix/v1/market/depth"

    # Proper symbol format for each market
    if market_type == "spot":
        formatted_symbol = f"{symbol}_SPBL"
    elif market_type == "futures":
        formatted_symbol = f"{symbol}_UMCBL"
    else:
        return None

    params = {"symbol": formatted_symbol, "limit": limit}
    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching {market_type} order book for {symbol}:", response.text)
        return None

# 📈 Fetch price data for indicators
def fetch_klines(symbol, interval):
    base_url = "https://api.bitget.com/api/mix/v1/market/candles"
    valid_intervals = {"1m": "60", "5m": "300", "15m": "900"}

    if interval not in valid_intervals:
        print(f"Invalid interval {interval} for symbol {symbol}")
        return None

    formatted_symbol = f"{symbol}_UMCBL"
    params = {"symbol": formatted_symbol, "granularity": valid_intervals[interval]}
    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        return response.json()["data"]
    else:
        print(f"Error fetching {symbol} {interval} klines:", response.text)
        return None

# ✅ Run the function
if __name__ == "__main__":
    all_symbols = fetch_all_altcoins()
    for symbol in all_symbols:
        fetch_order_book("futures", symbol)
        fetch_klines(symbol, "5m")
