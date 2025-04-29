import requests
import numpy as np
import time
import os
from ta.momentum
import RSIIndicator
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HEADERS = {
    'Accept': 'application/json',
    'User-Agent': 'Mozilla/5.0'
}

BASE_URL = "https://api.mexc.com"


def send_telegram_alert(message):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        try:
            requests.post(url, data=data)
        except:
            pass


def fetch_symbols():
    try:
        url = f"{BASE_URL}/api/v3/exchangeInfo"
        res = requests.get(url, headers=HEADERS, timeout=10)
        data = res.json()
        return [s['symbol'] for s in data['symbols'] if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING']
    except:
        return []


def fetch_kline(symbol, interval, limit=50):
    try:
        url = f"{BASE_URL}/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
        res = requests.get(url, headers=HEADERS, timeout=10)
        return res.json()
    except:
        return []


def fetch_orderbook(symbol):
    try:
        url = f"{BASE_URL}/api/v3/depth?symbol={symbol}&limit=5"
        res = requests.get(url, headers=HEADERS, timeout=10)
        return res.json()
    except:
        return None


def calculate_rsi(close_prices, period=14):
    if len(close_prices) < period:
        return []
    rsi = RSIIndicator(close=close_prices, window=period)
    return rsi.rsi().values


def detect_spike(candles):
    try:
        last_candle = candles[-1]
        prev_candle = candles[-2]
        last_close = float(last_candle[4])
        prev_close = float(prev_candle[4])
        change_pct = (last_close - prev_close) / prev_close * 100
        return abs(change_pct) >= 1.0
    except:
        return False


def analyze_symbol(symbol):
    candles_15m = fetch_kline(symbol, '15m', 50)
    candles_1h = fetch_kline(symbol, '1h', 50)

    if not candles_15m or not candles_1h:
        return None

    try:
        closes_15m = np.array([float(c[4]) for c in candles_15m if len(c) > 4])
        closes_1h = np.array([float(c[4]) for c in candles_1h if len(c) > 4])
        if len(closes_1h) < 20:
            return None

        rsi_15m = calculate_rsi(closes_15m)
        rsi_1h = calculate_rsi(closes_1h)

        last_rsi_15m = rsi_15m[-1] if len(rsi_15m) > 0 else 100
        last_rsi_1h = rsi_1h[-1] if len(rsi_1h) > 0 else 100

        if last_rsi_15m > 30 or last_rsi_1h > 35:
            return None

        if not detect_spike(candles_15m):
            return None

        orderbook = fetch_orderbook(symbol)
        if not orderbook or 'bids' not in orderbook or 'asks' not in orderbook:
            return None

        top_bid = float(orderbook['bids'][0][0])
        top_ask = float(orderbook['asks'][0][0])
        mark_price = (top_bid + top_ask) / 2

        suggestion = f"Buy zone: {top_bid:.4f} - {top_ask:.4f}"
        tp_zone = f"Target: {mark_price * 1.015:.4f}"

        message = f"[SPOT SIGNAL] {symbol}\nRSI 15m: {last_rsi_15m:.2f}, RSI 1h: {last_rsi_1h:.2f}\n{suggestion}\n{tp_zone}"
        send_telegram_alert(message)

        return True

    except Exception as e:
        print(f"Analysis error for {symbol}: {e}")
        return None


def main():
    print("Starting Strong Spot Signal Scanner (MEXC)...")
    symbols = fetch_symbols()
    print(f"[INFO] {len(symbols)} coins loaded.")
    while True:
        for symbol in symbols:
            try:
                analyze_symbol(symbol)
                time.sleep(1.2)
            except Exception as e:
                print(f"Main loop error: {e}")
        time.sleep(60)


if __name__ == "__main__":
    main()
