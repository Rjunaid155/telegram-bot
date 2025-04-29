import requests
import time
import numpy as np
from ta.momentum import RSIIndicator
import telegram
import os

# Environment variables
TELEGRAM_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = telegram.Bot(token=TELEGRAM_TOKEN)

def fetch_all_symbols():
    try:
        url = 'https://api.mexc.com/api/v3/exchangeInfo'
        response = requests.get(url, timeout=10)
        data = response.json()

        # Debug hata sakte ho ab
        # print("[DEBUG] Sample response keys:", list(data.keys()))
        # print("[DEBUG] First 3 symbols:", data.get('symbols', [])[:3])

        symbols = [s['symbol'] for s in data['symbols'] if s['quoteAsset'] == 'USDT' and s['isSpotTradingAllowed']]
        return symbols
    except Exception as e:
        print("[ERROR] Symbol fetch error:", e)
        return []

def fetch_kline(symbol, interval='15m', limit=50):
    try:
        url = f'https://api.mexc.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}'
        response = requests.get(url, timeout=10)
        data = response.json()

        if isinstance(data, list) and len(data) > 0:
            return data
        else:
            print(f"[DEBUG] {symbol}: No candle data for interval {interval}")
            return None
    except Exception as e:
        print(f"[ERROR] {symbol}: Failed to fetch candles ({interval}) => {e}")
        return None

def calculate_rsi(closes, period=14):
    try:
        indicator = RSIIndicator(close=pd.Series(closes), window=period)
        return indicator.rsi().values
    except Exception as e:
        print("[ERROR] RSI calculation error:", e)
        return []

def detect_spike(candles, threshold=1.0):
    try:
        if len(candles) < 2:
            return False
        last_close = float(candles[-2][4])
        current_close = float(candles[-1][4])
        change = ((current_close - last_close) / last_close) * 100
        return abs(change) >= threshold
    except Exception as e:
        print("[ERROR] Spike detection failed:", e)
        return False

def analyze_symbol(symbol):
    candles_15m = fetch_kline(symbol, '15m')
    candles_1h = fetch_kline(symbol, '1h')

    if not candles_15m or not candles_1h:
        print(f"[DEBUG] {symbol}: Candle data missing")
        return None

    try:
        closes_15m = np.array([float(c[4]) for c in candles_15m if len(c) > 4])
        closes_1h = np.array([float(c[4]) for c in candles_1h if len(c) > 4])
    except Exception as e:
        print(f"[DEBUG] {symbol}: Close parsing failed — {e}")
        return None

    if len(closes_15m) < 20 or len(closes_1h) < 20:
        print(f"[DEBUG] {symbol}: Insufficient candle length")
        return None

    rsi_15m = calculate_rsi(closes_15m)
    rsi_1h = calculate_rsi(closes_1h)

    if len(rsi_15m) < 1 or len(rsi_1h) < 1:
        print(f"[DEBUG] {symbol}: RSI data incomplete")
        return None

    last_rsi_15m = rsi_15m[-1]
    last_rsi_1h = rsi_1h[-1]

    print(f"[DEBUG] {symbol}: RSI 15m = {last_rsi_15m:.2f}, RSI 1h = {last_rsi_1h:.2f}")

    if last_rsi_15m > 30 or last_rsi_1h > 35:
        print(f"[DEBUG] {symbol}: RSI not oversold")
        return None

    if not detect_spike(candles_15m):
        print(f"[DEBUG] {symbol}: No spike detected")
        return None

    # All conditions passed
    return {
        "symbol": symbol,
        "rsi_15m": round(last_rsi_15m, 2),
        "rsi_1h": round(last_rsi_1h, 2)
    }

def send_telegram_alert(signal):
    msg = f"""[STRONG SPOT SIGNAL]
Symbol: {signal['symbol']}
RSI 15m: {signal['rsi_15m']}
RSI 1h: {signal['rsi_1h']}
"""
    try:
        bot.send_message(chat_id=CHAT_ID, text=msg)
        print(f"[ALERT SENT] {signal['symbol']}")
    except Exception as e:
        print("[ERROR] Telegram send failed:", e)

def main():
    print("Starting Strong Spot Signal Scanner (MEXC)...")
    symbols = fetch_all_symbols()
    print(f"[INFO] {len(symbols)} coins loaded.")
    for symbol in symbols:
        try:
            signal = analyze_symbol(symbol)
            if signal:
                send_telegram_alert(signal)
            time.sleep(0.4)
        except Exception as e:
            print("[ERROR]", e)

if __name__ == "__main__":
    import pandas as pd
    main()
