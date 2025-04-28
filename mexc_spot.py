import os
import time
import requests
import numpy as np
import traceback
from datetime import datetime
from statistics import mean

# Environment Variables
TELEGRAM_TOKEN = os.getenv('TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

MEXC_API_BASE = 'https://api.mexc.com'
SCAN_INTERVAL = 15  # seconds

# Functions
def send_telegram_message(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram not configured properly.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Telegram send error: {e}")

def fetch_symbols():
    try:
        response = requests.get(f"{MEXC_API_BASE}/api/v3/exchangeInfo", timeout=5)
        symbols = [s['symbol'] for s in response.json()['symbols'] if s['quoteAsset'] == 'USDT' and s['isSpotTradingAllowed']]
        return symbols
    except Exception as e:
        print(f"Symbol fetch error: {e}")
        return []

def fetch_kline(symbol, interval='15m', limit=50):
    try:
        response = requests.get(f"{MEXC_API_BASE}/api/v3/klines", params={'symbol': symbol, 'interval': interval, 'limit': limit}, timeout=5)
        return response.json()
    except:
        return []

def fetch_orderbook(symbol, limit=50):
    try:
        response = requests.get(f"{MEXC_API_BASE}/api/v3/depth", params={'symbol': symbol, 'limit': limit}, timeout=5)
        return response.json()
    except:
        return {}

def calculate_rsi(closes, period=14):
    deltas = np.diff(closes)
    seed = deltas[:period]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 0
    rsi = np.zeros_like(closes)
    rsi[:period] = 100. - 100. / (1. + rs)
    for i in range(period, len(closes)):
        delta = deltas[i - 1]
        upval = max(delta, 0)
        downval = -min(delta, 0)
        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period
        rs = up / down if down != 0 else 0
        rsi[i] = 100. - 100. / (1. + rs)
    return rsi

def detect_spike(candles):
    closes = np.array([float(c[4]) for c in candles])
    atr = np.mean(np.abs(np.diff(closes)))
    last_candle = closes[-1]
    prev_close = closes[-2]
    move = abs(last_candle - prev_close)
    return move > 1.2 * atr

def analyze_symbol(symbol):
    candles_15m = fetch_kline(symbol, '15m', 50)
    candles_1h = fetch_kline(symbol, '1h', 50)
    if not candles_15m or not candles_1h:
        return None

    closes_15m = np.array([float(c[4]) for c in candles_15m])
    closes_1h = np.array([float(c[4]) for c in candles_1h])

    rsi_15m = calculate_rsi(closes_15m)
    rsi_1h = calculate_rsi(closes_1h)

    last_rsi_15m = rsi_15m[-1]
    last_rsi_1h = rsi_1h[-1]

    if last_rsi_15m > 30 or last_rsi_1h > 35:
        return None

    if not detect_spike(candles_15m):
        return None

    orderbook = fetch_orderbook(symbol)
    if not orderbook or 'bids' not in orderbook or 'asks' not in orderbook:
        return None

    top_bids = sum(float(bid[1]) for bid in orderbook['bids'][:5])
    top_asks = sum(float(ask[1]) for ask in orderbook['asks'][:5])

    if top_bids < top_asks * 1.1:
        return None

    last_price = float(candles_15m[-1][4])
    entry_min = last_price * 0.998
    entry_max = last_price * 1.001

    tp1 = last_price * 1.012
    tp2 = last_price * 1.018

    message = f"""Spot Signal - Strong Buy

Coin: {symbol}
Entry Range: {entry_min:.6f} - {entry_max:.6f}
Target 1 (TP1): {tp1:.6f}
Target 2 (TP2): {tp2:.6f}
Orderbook Strength: Strong
Timeframes: 15min + 1H Confirmed
Protection: Dynamic SL below entry

#MEXC #Spot #Signal
"""

    return message

# Main
def main():
    print("Starting Strong Spot Signal Scanner (MEXC)...")
    symbols = fetch_symbols()
    print(f"[INFO] {len(symbols)} coins loaded.")

    while True:
        try:
            for symbol in symbols:
                signal = analyze_symbol(symbol)
                if signal:
                    print(f"[ALERT] Signal detected for {symbol}")
                    send_telegram_message(signal)
                time.sleep(1)
        except Exception as e:
            print(f"Main loop error: {e}")
            traceback.print_exc()
            time.sleep(5)

if __name__ == "__main__":
    main()
