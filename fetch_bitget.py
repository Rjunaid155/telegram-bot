import requests
import os
import hmac
import hashlib
import base64
import telebot
import pandas_ta as ta  # 🟢 pandas-ta for technical indicators
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# 🔑 Bitget API Keys
API_KEY = os.getenv("BITGET_API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
PASSPHRASE = os.getenv("BITGET_PASSPHRASE")
TELEGRAM_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# 🛠️ Signature generation
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

# 📊 Fetch candlestick data for indicators
def fetch_candle_data(symbol, market_type):
    if market_type == "spot":
        base_url = f"https://api.bitget.com/api/spot/v1/market/candles?symbol={symbol}_SPBL&limit=200"
    elif market_type == "futures":
        base_url = f"https://api.bitget.com/api/mix/v1/market/candles?symbol={symbol}_UMCBL&limit=200"
    else:
        return None

    response = requests.get(base_url)
    if response.status_code == 200:
        data = response.json()
        return pd.Series([float(candle[4]) for candle in data["data"]])  # Close prices as pandas series
    else:
        print(f"Error fetching candle data for {symbol}: {response.text}")
        return None

# 📈 Major Indicators
def calculate_indicators(symbol, market_type):
    close_prices = fetch_candle_data(symbol, market_type)

    if close_prices is not None:
        rsi = ta.rsi(close_prices, length=14)
        ema = ta.ema(close_prices, length=9)
        macd = ta.macd(close_prices, fast=12, slow=26, signal=9)
        bollinger = ta.bbands(close_prices, length=20, std=2)

        return {
            "RSI": rsi.iloc[-1],  # Latest value
            "EMA": ema.iloc[-1],
            "MACD": macd['MACD_12_26_9'].iloc[-1],
            "MACD_Signal": macd['MACDs_12_26_9'].iloc[-1],
            "UpperBand": bollinger['BBU_20_2.0'].iloc[-1],
            "LowerBand": bollinger['BBL_20_2.0'].iloc[-1]
        }
    return {}

# 📅 Calculate time to alert 5 minutes before trade execution
def get_alert_time():
    return (datetime.utcnow() + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')

# 📊 Fetch & Send Alerts
def check_and_alert():
    spot_pairs = get_all_trading_pairs("spot")
    futures_pairs = get_all_trading_pairs("futures")

    previous_prices = {}  # Store previous prices

    for symbol in spot_pairs + futures_pairs:
        market = "spot" if symbol in spot_pairs else "futures"
        data = fetch_order_book(market, symbol)

        if data and "data" in data and data["data"]["bids"]:
            best_bid = float(data["data"]["bids"][0][0])
            stop_loss = round(best_bid * 0.995, 4)
            take_profit = round(best_bid * 1.005, 4)

            # Indicators calculation
            indicators = calculate_indicators(symbol, market)

            # Entry position based on MACD and EMA for long/short
            entry_position = "Long" if indicators["MACD"] > indicators["MACD_Signal"] else "Short"

            alert_msg = (
                f"🚀 Coin Name: {symbol} ({market.upper()})\n"
                f"📊 Entry Position: {entry_position}\n"
                f"💵 Price: {best_bid}\n"
                f"📅 Date and Time: {get_alert_time()}\n"
                f"📉 Stop Loss: {stop_loss}\n"
                f"📈 Take Profit: {take_profit}\n"
                f"📊 RSI: {indicators['RSI']:.2f}, EMA: {indicators['EMA']:.2f}\n"
                f"📊 MACD: {indicators['MACD']:.2f}, Signal: {indicators['MACD_Signal']:.2f}\n"
                f"📊 Bollinger Bands: Upper: {indicators['UpperBand']:.2f}, Lower: {indicators['LowerBand']:.2f}"
            )

            send_telegram_alert(alert_msg)

# ✅ Run the function
if __name__ == "__main__":
    check_and_alert()
