import requests
import os
import telebot
from datetime import datetime, timedelta

# 🔑 Bitget API Keys
API_KEY = os.getenv("BITGET_API_KEY")
SECRET_KEY = os.getenv("BITGET_SECRET_KEY")
PASSPHRASE = os.getenv("BITGET_PASSPHRASE")
TELEGRAM_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# 📊 Fetch top gainers and losers from Bitget
def fetch_top_gainers_losers():
    url = "https://api.bitget.com/api/spot/v1/market/ticker"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()["data"]
        sorted_data = sorted(data, key=lambda x: float(x["changeRate"]), reverse=True)

        gainers = sorted_data[:5]  # Top 5 gainers
        losers = sorted_data[-5:]  # Bottom 5 losers

        return gainers, losers
    else:
        print(f"Error fetching market data: {response.text}")
        return [], []

# 🛠️ Function to generate current time + 5 minutes for alerts
def get_alert_time():
    return (datetime.utcnow() + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')

# 🔔 Send alerts to Telegram
def send_telegram_alert(message):
    bot.send_message(CHAT_ID, message)

# 🚀 Fetch & Send Alerts for Top Gainers and Losers
def check_and_alert():
    gainers, losers = fetch_top_gainers_losers()

    # Alert for gainers
    for gainer in gainers:
        symbol = gainer["symbol"]
        last_price = gainer["last"]
        alert_msg = (
            f"🚀 Top Gainer Alert: {symbol}\n"
            f"⏰ Alert for: {get_alert_time()} (5 minutes early)\n"
            f"📊 Last Price: {last_price}\n"
            f"🔝 This coin is pumping with high volume!"
        )
        send_telegram_alert(alert_msg)

    # Alert for losers
    for loser in losers:
        symbol = loser["symbol"]
        last_price = loser["last"]
        alert_msg = (
            f"⚠️ Top Loser Alert: {symbol}\n"
            f"⏰ Alert for: {get_alert_time()} (5 minutes early)\n"
            f"📊 Last Price: {last_price}\n"
            f"🔻 This coin is dumping with high volume!"
        )
        send_telegram_alert(alert_msg)

# ✅ Run the function
if __name__ == "__main__":
    check_and_alert()
