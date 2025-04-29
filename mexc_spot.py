import requests
import time
import pandas as pd
from ta.momentum import RSIIndicator
from datetime import datetime
import pytz
import telebot
import os

# --- CONFIG ---
API_URL = "https://api.mexc.com"
TELEGRAM_TOKEN = "TOKEN"
CHAT_ID = "TELEGRAM_CHAT_ID"
INTERVAL_15M = "15m"
INTERVAL_1H = "1h"

bot = telebot.TeleBot(TOKEN)

def send_alert(message):
    bot.send_message(CHAT_ID, message)

def fetch_symbols():
    url = f"{API_URL}/api/v3/exchangeInfo"
    data = requests.get(url).json()
    symbols = [s['symbol'] for s in data['symbols'] if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING']
    return symbols

def fetch_ohlcv(symbol, interval, limit=100):
    url = f"{API_URL}/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base', 'taker_buy_quote', 'ignore'
        ])
    return None

def analyze_symbol(symbol):
    candles_15m = fetch_ohlcv(symbol, INTERVAL_15M)
    candles_1h = fetch_ohlcv(symbol, INTERVAL_1H)

    if candles_15m is None or candles_1h is None or len(candles_15m) < 20 or len(candles_1h) < 20:
        return

    candles_15m['close'] = candles_15m['close'].astype(float)
    candles_1h['close'] = candles_1h['close'].astype(float)

    rsi_15m = RSIIndicator(close=candles_15m['close'], window=14).rsi()
    rsi_1h = RSIIndicator(close=candles_1h['close'], window=14).rsi()

    last_rsi_15m = rsi_15m.iloc[-1]
    last_rsi_1h = rsi_1h.iloc[-1]

    current_price = candles_15m['close'].iloc[-1]
    entry_price = round(current_price * 1.001, 4)  # 0.1% above current
    take_profit = round(entry_price * 1.01, 4)     # 1% TP

    if 20 <= last_rsi_15m <= 25:
        confirmations = []

        if last_rsi_1h < 30:
            confirmations.append("1h RSI Oversold")
        else:
            confirmations.append("1h RSI Not Oversold")

        # Optional ATR / volume spike can be added here

        message = (
            f"*[SPOT BUY SIGNAL]*\n"
            f"Symbol: {symbol}\n"
            f"RSI 15m: {last_rsi_15m:.2f}\n"
            f"RSI 1h: {last_rsi_1h:.2f}\n"
            f"{' | '.join(confirmations)}\n"
            f"Entry: {entry_price}\n"
            f"Target TP: {take_profit}\n"
            f"Time: {datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )
        send_alert(message)

def main():
    print("Starting Strong Spot Signal Scanner (MEXC)...")
    symbols = fetch_symbols()
    print(f"[INFO] {len(symbols)} coins loaded.")
    
    while True:
        for symbol in symbols:
            if symbol.endswith("USDT"):
                try:
                    analyze_symbol(symbol)
                except Exception as e:
                    print(f"[ERROR] {symbol}: {e}")
        time.sleep(60)

if __name__ == "__main__":
    main()
