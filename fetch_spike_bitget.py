import requests
import os
import telebot
from datetime import datetime, timedelta

# 🔑 Bitget API Keys (Render ke environment variables se le raha hai)
API_KEY = os.getenv("BITGET_API_KEY")
SECRET_KEY = os.getenv("BITGET_SECRET_KEY")
PASSPHRASE = os.getenv("BITGET_PASSPHRASE")  # Futures trading ke liye zaroori hai
TELEGRAM_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# 📊 Function to fetch order book (Spot & Futures)
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

# 📊 Function to check for spike alerts based on price change and volume increase
def check_spike_alert(symbol, market, prev_price, current_price, prev_volume, current_volume):
    price_change = ((current_price - prev_price) / prev_price) * 100
    volume_change = ((current_volume - prev_volume) / prev_volume) * 100 if prev_volume != 0 else 0

    # Spike threshold: Price change ≥ 3% and Volume increase ≥ 50%
    if abs(price_change) >= 3 and volume_change >= 50:
        direction = "Bullish" if price_change > 0 else "Bearish"
        position = "Long" if price_change > 0 else "Short"  # 🟢 Add Long/Short based on price movement
        alert_msg = (
            f"🚨 {symbol} ({market.upper()}) Spike Detected:\n"
            f"📊 Price Change: {round(price_change, 2)}% {direction} Move!\n"
            f"📈 Volume Change: {round(volume_change, 2)}% Increase!\n"
            f"🟩 Position: {position} Signal"  # 🟩 Position Alert: Long/Short
        )
        send_telegram_alert(alert_msg)

# 🛠️ Function to generate current time + 5 minutes for alerts
def get_alert_time():
    return (datetime.utcnow() + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')

# 🚀 Fetch & Send Spike Alerts
def check_and_alert():
    spot_pairs = get_all_trading_pairs("spot")
    futures_pairs = get_all_trading_pairs("futures")

    previous_prices = {}  # 📌 Store previous prices for spike alerts
    previous_volumes = {}  # 📌 Store previous volumes

    for symbol in spot_pairs + futures_pairs:
        market = "spot" if symbol in spot_pairs else "futures"
        data = fetch_order_book(market, symbol)

        if data and "data" in data and data["data"]["bids"] and data["data"]["asks"]:  # 🛡️ Check if bids/asks list is not empty
            best_bid = float(data["data"]["bids"][0][0])  # ✅ Best buy price
            volume = sum(float(order[1]) for order in data["data"]["bids"])  # Calculate total volume from bids

            if symbol in previous_prices and symbol in previous_volumes:
                check_spike_alert(symbol, market, previous_prices[symbol], best_bid, previous_volumes[symbol], volume)

            # 🔄 Update previous price and volume
            previous_prices[symbol] = best_bid
            previous_volumes[symbol] = volume
        else:
            print(f"No valid data for {symbol} in {market}, skipping...")

# ✅ Run the function
if __name__ == "__main__":
    check_and_alert()
