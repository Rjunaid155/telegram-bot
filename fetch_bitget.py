import requests
import time
import os
import hmac
import hashlib
import base64
import telebot

# 🔑 Bitget API Keys (Render ke environment variables se le raha hai)
API_KEY = os.getenv("BITGET_API_KEY")
SECRET_KEY = os.getenv("BITGET_SECRET_KEY")
PASSPHRASE = os.getenv("BITGET_PASSPHRASE")  # Futures trading ke liye zaroori hai
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
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

# ⚡ Spike Trading Alert Function
def check_spike_trading(symbol, market, current_price, prev_price):
    price_change = ((current_price - prev_price) / prev_price) * 100

    if price_change >= 2:  # 🟢 2% ya zyada bullish spike
        alert_msg = f"🚀 {symbol} ({market.upper()}) Spike Alert: +{round(price_change, 2)}% Bullish Move!"
        send_telegram_alert(alert_msg)
    elif price_change <= -2:  # 🔴 2% ya zyada bearish spike
        alert_msg = f"⚠️ {symbol} ({market.upper()}) Spike Alert: {round(price_change, 2)}% Bearish Move!"
        send_telegram_alert(alert_msg)

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
            stop_loss = round(best_bid * 0.98, 4)  # 🔻 2% Neeche Stop Loss
            take_profit = round(best_bid * 1.02, 4)  # 🔺 2% Upar Take Profit
            
            alert_msg = (
                f"🔥 {symbol} ({market.upper()}) Trading Signal:\n"
                f"📌 Entry Price: {best_bid}\n"
                f"📉 Stop Loss: {stop_loss}\n"
                f"📈 Take Profit: {take_profit}"
            )
            send_telegram_alert(alert_msg)

            # 📊 Spike Trading Alert Check
            if symbol in previous_prices:
                check_spike_trading(symbol, market, best_bid, previous_prices[symbol])
            
            previous_prices[symbol] = best_bid  # 🔄 Update previous price

# ✅ Run the function
if _name_ == "_main_":
    check_and_alert()
