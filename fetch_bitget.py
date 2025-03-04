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
SECRET_KEY = os.getenv("SECRET_KEY")
PASSPHRASE = os.getenv("BITGET_PASSPHRASE")
TELEGRAM_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# 🛠️ Signature generation function (v2)
def generate_signature(timestamp, method, request_path, body=""):
    message = f"{timestamp}{method}{request_path}{body}"
    signature = hmac.new(SECRET_KEY.encode(), message.encode(), hashlib.sha256).digest()
    return base64.b64encode(signature).decode()

# 📊 Function to fetch order book (Spot & Futures) using correct API URLs
def fetch_order_book(market_type, symbol, limit=5):
    if market_type == "spot":
        base_url = "https://api.bitget.com/api/spot/v1/market/depth"
        symbol = f"{symbol}_SPBL"  # ✅ Spot ke liye symbol format
    elif market_type == "futures":
        base_url = "https://api.bitget.com/api/mix/v1/market/depth"
        symbol = f"{symbol}_UMCBL"  # ✅ Futures ke liye symbol format
    else:
        return None

    params = {"symbol": symbol, "limit": limit}
    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching {market_type} order book:", response.text)
        return None

# 🔍 Function to get all trading pairs using correct API URLs
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

# 📅 Calculate time to alert 5 minutes before trade execution
def get_alert_time():
    return (datetime.utcnow() + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')

# 🚀 Fetch & Send Alerts
def check_and_alert():
    spot_pairs = get_all_trading_pairs("spot")
    futures_pairs = get_all_trading_pairs("futures")

    previous_prices = {}  # 📌 Store previous prices for spike alerts

    for symbol in spot_pairs + futures_pairs:
        market = "spot" if symbol in spot_pairs else "futures"
        data = fetch_order_book(market, symbol)

        if data:
            best_bid = float(data["data"]["bids"][0][0])  # ✅ Best buy price
            stop_loss = round(best_bid * 0.995, 4)  # 🔻 0.5% Neeche Stop Loss
            take_profit = round(best_bid * 1.005, 4)  # 🔺 0.5% Upar Take Profit

            # Define entry position based on trend (short or long)
            entry_position = "Short" if best_bid < previous_prices.get(symbol, best_bid) else "Long"
            
            # Format message as seen in image
            alert_msg = (
                f"Coin Name: {symbol}\n"
                f"Entry Position: {entry_position}\n"
                f"Coin Value: {best_bid}\n"
                f"Date and Time: {get_alert_time()}\n"
                f"Note: Manage your risk; any trade can fail. Bitnode coordinate 888'12''65\n"
            )
            send_telegram_alert(alert_msg)

            # 📊 Spike Trading Alert Check
            if symbol in previous_prices:
                price_change = ((best_bid - previous_prices[symbol]) / previous_prices[symbol]) * 100
                if price_change >= 0.5:
                    send_telegram_alert(f"🚀 {symbol} Bullish spike detected!")
                elif price_change <= -0.5:
                    send_telegram_alert(f"⚠️ {symbol} Bearish spike detected!")

            previous_prices[symbol] = best_bid  # 🔄 Update previous price

# ✅ Run the function
if __name__ == "__main__":
    check_and_alert()
