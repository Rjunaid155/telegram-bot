import requests
import pandas as pd
import time
from telegram import Bot

# MEXC API Endpoint
MEXC_API_URL = 'https://api.mexc.com/api/v2/market/ticker'

# Telegram Bot Token & Chat ID
TELEGRAM_BOT_TOKEN = 'TOKEN'
CHAT_ID = 'YOUR_CHAT_ID'

# Define the percentage change for alert trigger
PRICE_CHANGE_THRESHOLD = 2.5  # in percentage

# Fetch Market Data from MEXC
def fetch_market_data():
    response = requests.get(MEXC_API_URL)
    if response.status_code == 200:
        data = response.json()
        return data['data']
    else:
        print("Error fetching data from MEXC API")
        return []

# Detect significant price spike (based on percentage)
def detect_spike(data):
    for coin in data:
        symbol = coin['symbol']
        price = float(coin['lastPrice'])
        high_price = float(coin['highPrice'])
        low_price = float(coin['lowPrice'])
        
        # Calculate the percentage change from high and low prices
        price_change = (high_price - low_price) / low_price * 100
        
        if price_change >= PRICE_CHANGE_THRESHOLD:
            return symbol, price_change
    return None, None

# Send Telegram Alert
def send_telegram_alert(symbol, price_change):
    message = f"Alert: {symbol} has shown a significant price move of {price_change:.2f}%."
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    bot.send_message(chat_id=CHAT_ID, text=message)
    print(f"Alert sent: {message}")

# Main Function to Monitor Market
def monitor_market():
    while True:
        market_data = fetch_market_data()
        if market_data:
            symbol, price_change = detect_spike(market_data)
            if symbol and price_change:
                send_telegram_alert(symbol, price_change)
        
        # Wait for 1 minute before next check
        time.sleep(60)

# Run the monitoring process
if __name__ == "__main__":
    monitor_market()
