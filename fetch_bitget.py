import os
import requests
import numpy as np
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
from telegram import Bot
from bitcoinrpc.authproxy import AuthServiceProxy

# 🔑 API & Telegram Config
API_KEY = os.getenv("BITGET_API_KEY")
SECRET_KEY = os.getenv("BITGET_SECRET_KEY")
PASSPHRASE = os.getenv("BITGET_PASSPHRASE")
TELEGRAM_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 🚀 Bitcoin Core RPC Config
RPC_USER = os.getenv("RPC_USER")
RPC_PASSWORD = os.getenv("RPC_PASSWORD")
RPC_PORT = os.getenv("RPC_PORT")
RPC_HOST = "127.0.0.1"

bot = Bot(token=TELEGRAM_TOKEN)

# 📊 *Fetch Order Book Data*
def fetch_order_book(symbol, market_type):
    if market_type == "spot":
        symbol = f"{symbol.replace('USDT', '')}USDT_SPBL"
    elif market_type == "futures":
        symbol = f"{symbol.replace('USDT', '')}USDT_UMCBL"
    
    url = f"https://api.bitget.com/api/mix/v1/market/depth"
    params = {"symbol": symbol, "limit": 5}
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"⚠️ Order book fetch error: {response.text}")
        return None

# 📈 *Fetch Candlestick Data*
def fetch_klines(symbol, interval):
    url = "https://api.bitget.com/api/mix/v1/market/candles"
    valid_intervals = {"1m": "60", "5m": "300", "15m": "900"}
    
    params = {"symbol": symbol, "granularity": valid_intervals[interval]}
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        return response.json()["data"]
    else:
        print(f"⚠️ Error fetching {symbol} {interval} klines: {response.text}")
        return None

# 📊 *Calculate Indicators*
def calculate_indicators(data):
    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["close"] = df["close"].astype(float)

    df["rsi"] = ta.rsi(df["close"], length=14)
    df["macd"], df["signal"], _ = ta.macd(df["close"])
    df["bollinger_high"], df["bollinger_mid"], df["bollinger_low"] = ta.bbands(df["close"], length=20)
    df["atr"] = ta.atr(df["high"], df["low"], df["close"], length=14)

    return df.iloc[-1]  # Latest Indicator Values

# 🚀 *Mempool Data Analysis*
def fetch_mempool_data():
    try:
        rpc_conn = AuthServiceProxy(f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}")
        mempool_info = rpc_conn.getmempoolinfo()
        return mempool_info
    except Exception as e:
        print(f"⚠️ Error fetching mempool data: {e}")
        return None

# 📉 *Generate Trade Levels*
def generate_trade_levels(entry_price):
    stop_loss = round(entry_price * 0.98, 5)
    take_profit = round(entry_price * 1.05, 5)
    exit_price = round(entry_price * 1.03, 5)
    return stop_loss, take_profit, exit_price

# 🔔 *Send Telegram Alerts*
def send_telegram_alert(message):
    bot.send_message(CHAT_ID, message)

# ✅ *Check & Generate Trading Signals*
def check_and_alert():
    symbols = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "SOLUSDT", "ADAUSDT", "DOGEUSDT", "LINKUSDT"]
    timeframes = ["1m", "5m", "15m"]

    for symbol in symbols:
        for market in ["spot", "futures"]:
            order_book = fetch_order_book(symbol, market)
            if order_book:
                best_bid = float(order_book["data"]["bids"][0][0])
                best_ask = float(order_book["data"]["asks"][0][0])
                entry_price = best_bid

                stop_loss, take_profit, exit_price = generate_trade_levels(entry_price)
                trend = "📈 Long" if best_bid > best_ask else "📉 Short"
                execution_time = datetime.utcnow() + timedelta(minutes=15)

                message = (
                    f"🔥 {symbol} ({market.upper()}) Trade Signal:\n"
                    f"{trend}\n"
                    f"📌 Entry Price: {entry_price}\n"
                    f"🎯 Take Profit (TP): {take_profit}\n"
                    f"🚪 Exit Price: {exit_price}\n"
                    f"🛑 Stop Loss (SL): {stop_loss}\n"
                    f"⏳ Execution Time: {execution_time.strftime('%H:%M:%S UTC')}"
                )
                send_telegram_alert(message)

            for tf in timeframes:
                klines = fetch_klines(symbol, tf)
                if klines:
                    indicators = calculate_indicators(klines)
                    message = (
                        f"📊 {symbol} ({market.upper()}) {tf} Timeframe:\n"
                        f"🔹 RSI: {indicators['rsi']:.2f}\n"
                        f"📊 MACD: {indicators['macd']:.2f}\n"
                        f"📈 Bollinger Bands: {indicators['bollinger_high']:.2f} / {indicators['bollinger_low']:.2f}\n"
                        f"⚡ ATR: {indicators['atr']:.2f}"
                    )
                    send_telegram_alert(message)

    # *Mempool Data Analysis*
    mempool_info = fetch_mempool_data()
    if mempool_info:
        mempool_alert = (
            f"🚀 Mempool Data:\n"
            f"🔹 TX Count: {mempool_info['size']}\n"
            f"⏳ Min Fee: {mempool_info['mempoolminfee']:.8f} BTC"
        )
        send_telegram_alert(mempool_alert)

# ✅ *Run the Script*
if __name__ == "__main__":
    check_and_alert()
