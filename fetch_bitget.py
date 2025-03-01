import requests
import time
import os
import hmac
import hashlib
import base64

# 🔑 Bitget API Keys (Render ke environment variables se le raha hai)
API_KEY = os.getenv("BITGET_API_KEY")
SECRET_KEY = os.getenv("BITGET_SECRET_KEY")
PASSPHRASE = os.getenv("BITGET_PASSPHRASE")  # Futures trading ke liye zaroori hai

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

# 🔔 Send alerts to Telegram
import telebot

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TELEGRAM_TOKEN)

def send_telegram_alert(message):
    bot.send_message(CHAT_ID, message)

# 🚀 Fetch & Send Alerts
def check_and_alert():
    symbols = ["BTCUSDT", "ETHUSDT", "XRPUSDT"]  # 🔄 Jitne chaho symbols add karo
    for symbol in symbols:
        for market in ["spot", "futures"]:
            data = fetch_order_book(market, symbol)
            if data:
                price = data["data"]["bids"][0][0]  # 🏷️ Sabse best buy price
                alert_msg = f"🔥 {symbol} ({market.upper()}) Order Book Update:\nBest Bid Price: {price}"
                send_telegram_alert(alert_msg)

# ✅ Run the function
if __name__ == "__main__":
    check_and_alert()
