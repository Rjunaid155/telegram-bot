import requests
import numpy as np
import time
from ta.momentum import RSIIndicator
import pandas as pd

TELEGRAM_TOKEN = 'TOKEN'
CHAT_ID = 'TELEGRAM_CHAT_ID'

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"[ERROR] Telegram Error: {e}")

def fetch_symbols():
    try:
        url = "https://api.mexc.com/api/v3/exchangeInfo"
        response = requests.get(url)
        data = response.json()
        symbols = [s['symbol'] for s in data['symbols']
                   if s['quoteAsset'] == 'USDT' and s['isSpotTradingAllowed']]
        print(f"[INFO] {len(symbols)} coins loaded.")
        return symbols
    except Exception as e:
        print(f"[ERROR] Symbol Fetch Error: {e}")
        return []

def fetch_kline(symbol, interval, limit=50):
    try:
        url = f"https://api.mexc.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
        res = requests.get(url)
        data = res.json()
        if isinstance(data, list) and len(data) > 0:
            return data
        else:
            return None
    except:
        return None

def calculate_rsi(closes, period=14):
    if len(closes) < period:
        return np.array([])
    return RSIIndicator(pd.Series(closes), window=period).rsi().values

def detect_spike(candles):
    try:
        if len(candles) < 2:
            return False
        current = float(candles[-1][4])
        previous = float(candles[-2][4])
        change = (current - previous) / previous * 100
        return change >= 1
    except:
        return False

def fetch_orderbook(symbol):
    try:
        url = f"https://api.mexc.com/api/v3/depth?symbol={symbol}&limit=20"
        res = requests.get(url)
        return res.json()
    except:
        return None

def detect_orderbook_imbalance(orderbook):
    try:
        bids = sum(float(b[1]) for b in orderbook['bids'])
        asks = sum(float(a[1]) for a in orderbook['asks'])
        return bids > asks * 1.5
    except:
        return False

def analyze_symbol(symbol):
    candles_15m = fetch_kline(symbol, '15m', 50)
    candles_1h = fetch_kline(symbol, '1h', 50)

    if not candles_15m:
        print(f"[DEBUG] {symbol}: Missing 15m candles")
        return None

    closes_15m = np.array([float(c[4]) for c in candles_15m])
    rsi_15m = calculate_rsi(closes_15m)
    if len(rsi_15m) == 0:
        return None
    last_rsi_15m = rsi_15m[-1]

    rsi_1h_text = "MISSING"
    rsi_1h_val = None
    signal_type = "Partial"

    if candles_1h and len(candles_1h) >= 20:
        closes_1h = np.array([float(c[4]) for c in candles_1h])
        rsi_1h = calculate_rsi(closes_1h)
        if len(rsi_1h) > 0:
            rsi_1h_val = rsi_1h[-1]
            rsi_1h_text = f"{rsi_1h_val:.2f}"
            signal_type = "Full"

    if last_rsi_15m > 25:
        return None
    if rsi_1h_val and rsi_1h_val > 35:
        return None

    if not detect_spike(candles_15m):
        return None

    orderbook = fetch_orderbook(symbol)
    if not orderbook or not detect_orderbook_imbalance(orderbook):
        return None

    print(f"[DEBUG] {symbol}: RSI_15m={last_rsi_15m:.2f}, RSI_1h={rsi_1h_text}, Type={signal_type}")

    return {
        'symbol': symbol,
        'rsi_15m': round(last_rsi_15m, 2),
        'rsi_1h': rsi_1h_text,
        'type': signal_type
    }

def main_loop():
    print("Starting Strong Spot Signal Scanner (MEXC)...")
    symbols = fetch_symbols()
    for symbol in symbols:
        try:
            result = analyze_symbol(symbol)
            if result:
                msg = (f"[SPOT BUY] Symbol: {result['symbol']} | RSI 15m: {result['rsi_15m']} | "
                       f"RSI 1h: {result['rsi_1h']} | Spike + OB Confirmed | Type: {result['type']}")
                send_telegram_message(msg)
        except Exception as e:
            print(f"[ERROR] {symbol}: {e}")

if __name__ == "__main__":
    while True:
        main_loop()
        time.sleep(300)  # run every 5 minutes
