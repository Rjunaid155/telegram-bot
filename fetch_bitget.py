import requests
import time
import os
import hmac
import hashlib
import base64
import telebot
import numpy as np

# 🔑 Bitget API Keys
API_KEY = os.getenv("BITGET_API_KEY")
SECRET_KEY = os.getenv("BITGET_SECRET_KEY")
PASSPHRASE = os.getenv("BITGET_PASSPHRASE")
TELEGRAM_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# 📊 Function to fetch order book (With Whale Detection)
def fetch_order_book(market_type, symbol, limit=10):
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
        data = response.json()
        best_bid = float(data["data"]["bids"][0][0])  
        best_ask = float(data["data"]["asks"][0][0])  
        whale_buyers = sum([float(x[1]) for x in data["data"]["bids"][:3]])  
        whale_sellers = sum([float(x[1]) for x in data["data"]["asks"][:3]])

        return best_bid, best_ask, whale_buyers, whale_sellers
    else:
        print(f"Error fetching {market_type} order book:", response.text)
        return None

# 📈 Fetch price data for indicators
def fetch_klines(symbol, interval):
    base_url = "https://api.bitget.com/api/mix/v1/market/candles"
    params = {"symbol": symbol, "granularity": interval}
    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        return response.json()["data"]
    else:
        print(f"Error fetching {symbol} {interval} klines:", response.text)
        return None

# 📊 Calculate MA, RSI (14), MACD (12,26,9)
def calculate_indicators(data):
    close_prices = np.array([float(candle[4]) for candle in data])

    # 📌 Moving Averages
    ma_10 = np.mean(close_prices[-10:])
    ma_50 = np.mean(close_prices[-50:])

    # 📌 RSI Calculation (14)
    deltas = np.diff(close_prices)
    gain = np.where(deltas > 0, deltas, 0)
    loss = np.where(deltas < 0, -deltas, 0)

    avg_gain = np.mean(gain[-14:])
    avg_loss = np.mean(loss[-14:])
    rs = avg_gain / avg_loss if avg_loss > 0 else 100
    rsi = 100 - (100 / (1 + rs))

    # 📌 MACD (12,26,9)
    ema_12 = np.mean(close_prices[-12:])
    ema_26 = np.mean(close_prices[-26:])
    macd = ema_12 - ema_26
    signal = np.mean(close_prices[-9:])
    macd_histogram = macd - signal

    return ma_10, ma_50, rsi, macd, macd_histogram

# 🚀 Detect Spike Movements (With Volume Confirmation)
def detect_spike(data):
    latest_close = float(data[-1][4])
    prev_close = float(data[-2][4])
    latest_volume = float(data[-1][5])  
    prev_volume = float(data[-2][5])

    spike_threshold = 1.5  
    volume_threshold = 2  

    price_change = ((latest_close - prev_close) / prev_close) * 100
    volume_change = latest_volume / (prev_volume + 1e-6)

    if abs(price_change) >= spike_threshold and volume_change >= volume_threshold:
        return "⚡ SPIKE ALERT: Sudden Price & Volume Surge Detected!"
    return None

# 🔥 ATR-Based SL, TP, Entry, Exit
def generate_trade_levels(entry_price, atr):
    stop_loss = entry_price - (atr * 2)  
    take_profit = entry_price + (atr * 3)  
    exit_price = entry_price + (atr * 2.5)  

    return stop_loss, take_profit, exit_price

# 🔔 Send alerts to Telegram
def send_telegram_alert(message):
    bot.send_message(CHAT_ID, message)

# 🚀 Fetch & Send Alerts (Advanced)
def check_and_alert():
    symbols = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "SOLUSDT", "ADAUSDT", "DOGEUSDT", "MATICUSDT"]
    timeframes = {"1m": 60, "5m": 300, "15m": 900}

    for symbol in symbols:
        for market in ["spot", "futures"]:
            order_data = fetch_order_book(market, symbol)
            if order_data:
                best_bid, best_ask, whale_buyers, whale_sellers = order_data
                entry_price = best_bid

                atr = abs(best_bid - best_ask)  
                stop_loss, take_profit, exit_price = generate_trade_levels(entry_price, atr)

                trend = "📈 Long" if whale_buyers > whale_sellers else "📉 Short"

                message = (
                    f"🔥 {symbol} ({market.upper()}) Trade Signal:\n"
                    f"{trend}\n"
                    f"📌 Entry Price: {entry_price:.2f}\n"
                    f"🎯 Take Profit (TP): {take_profit:.2f}\n"
                    f"🚪 Exit Price: {exit_price:.2f}\n"
                    f"🛑 Stop Loss (SL): {stop_loss:.2f}\n"
                    f"🐋 Whale Buyers: {whale_buyers:.2f} | 🐋 Whale Sellers: {whale_sellers:.2f}"
                )
                send_telegram_alert(message)

            for tf, seconds in timeframes.items():
                klines = fetch_klines(symbol, seconds)
                if klines:
                    ma_10, ma_50, rsi, macd, macd_hist = calculate_indicators(klines)
                    spike_alert = detect_spike(klines)

                    signal_msg = (
                        f"📊 {symbol} ({market.upper()}) {tf} Timeframe:\n"
                        f"🔹 MA-10: {ma_10:.2f} | MA-50: {ma_50:.2f}\n"
                        f"🔸 RSI(14): {rsi:.2f}\n"
                        f"📊 MACD: {macd:.2f} | Histogram: {macd_hist:.2f}"
                    )
                    send_telegram_alert(signal_msg)

                    if spike_alert:
                        send_telegram_alert(spike_alert)

# ✅ Run the function
if __name__ == "__main__":
    check_and_alert()
