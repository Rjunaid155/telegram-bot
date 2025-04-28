import requests
import time
import pandas as pd
import numpy as np
import ta
from datetime import datetime
import os
# ========== USER SETTINGS ==========
RSI_OVERSOLD_THRESHOLD = 28
MIN_STRENGTH_RATING = 85  # % minimum strength
ATR_MULTIPLIER = 1.5      # Spike confirmation factor
SCAN_INTERVAL = 30        # seconds between scans
SYMBOLS_LIMIT = 300       # Max symbols to scan
MEXC_BASE_URL = "https://api.mexc.com"

# Telegram settings (Optional)
TELEGRAM_TOKEN = "TOKEN"
CHAT_ID = "TELEGRAM_chat_id"

# ========== FUNCTIONS ==========

def fetch_symbols():
    try:
        url = f"{MEXC_BASE_URL}/api/v3/exchangeInfo"
        res = requests.get(url, timeout=10)
        data = res.json()
        symbols = [s['symbol'] for s in data['symbols'] if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING']
        return symbols[:SYMBOLS_LIMIT]
    except Exception as e:
        print(f"[ERROR] Symbol fetch error: {e}")
        return []

def fetch_klines(symbol, interval='15m', limit=100):
    try:
        url = f"{MEXC_BASE_URL}/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
        res = requests.get(url, timeout=10)
        data = res.json()
        df = pd.DataFrame(data, columns=['time','open','high','low','close','volume','c1','c2','c3','c4','c5'])
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['volume'] = df['volume'].astype(float)
        return df
    except Exception as e:
        print(f"[ERROR] Kline fetch error {symbol}: {e}")
        return None

def calculate_indicators(df):
    df['rsi'] = ta.momentum.RSIIndicator(close=df['close'], window=14).rsi()
    df['atr'] = ta.volatility.AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=14).average_true_range()
    return df

def fetch_orderbook(symbol):
    try:
        url = f"{MEXC_BASE_URL}/api/v3/depth?symbol={symbol}&limit=50"
        res = requests.get(url, timeout=10)
        data = res.json()
        bids = np.array([float(b[1]) for b in data['bids']])
        asks = np.array([float(a[1]) for a in data['asks']])
        total_bids = np.sum(bids)
        total_asks = np.sum(asks)
        bias = "UP" if total_bids > total_asks * 1.2 else "NEUTRAL"
        return bias
    except Exception as e:
        print(f"[ERROR] Orderbook fetch error {symbol}: {e}")
        return "UNKNOWN"

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        requests.post(url, data=payload)
    except Exception as e:
        print(f"[ERROR] Telegram send error: {e}")

def calculate_strength(rsi_score, atr_score, bias_score):
    return (rsi_score + atr_score + bias_score) / 3

# ========== MAIN SCANNER ==========

def scan():
    print("Starting Strong Spot Signal Scanner (MEXC)...")
    symbols = fetch_symbols()
    print(f"[INFO] Scanning {len(symbols)} coins...")

    while True:
        for symbol in symbols:
            try:
                df_15m = fetch_klines(symbol, '15m')
                df_1h = fetch_klines(symbol, '1h')

                if df_15m is None or df_1h is None:
                    continue

                df_15m = calculate_indicators(df_15m)
                df_1h = calculate_indicators(df_1h)

                latest_rsi_15m = df_15m['rsi'].iloc[-1]
                latest_rsi_1h = df_1h['rsi'].iloc[-1]

                latest_atr_15m = df_15m['atr'].iloc[-1]
                current_close = df_15m['close'].iloc[-1]
                previous_close = df_15m['close'].iloc[-2]

                # Conditions
                rsi_condition = (latest_rsi_15m <= RSI_OVERSOLD_THRESHOLD) and (latest_rsi_1h <= RSI_OVERSOLD_THRESHOLD)
                atr_condition = (current_close - previous_close) >= (latest_atr_15m * ATR_MULTIPLIER)

                if rsi_condition:
                    bias = fetch_orderbook(symbol)
                    bias_score = 100 if bias == "UP" else 50

                    # Strength calculation
                    rsi_score = 100 - latest_rsi_15m  # lower RSI -> stronger buy signal
                    atr_score = min(100, (current_close - previous_close) / latest_atr_15m * 100)

                    strength = calculate_strength(rsi_score, atr_score, bias_score)

                    if strength >= MIN_STRENGTH_RATING:
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        # TP Calculation
                        tp1 = round(current_close * 1.004, 4)
                        tp2 = round(current_close * 1.007, 4)

                        message = f"🔥 Strong Buy Signal 🔥\n\n"\
                                  f"Symbol: {symbol}\n"\
                                  f"Entry Price: {current_close}\n"\
                                  f"TP1: {tp1}\n"\
                                  f"TP2: {tp2}\n"\
                                  f"Strength: {strength:.2f}%\n"\
                                  f"Orderbook Bias: {bias}\n"\
                                  f"Time: {now}"

                        print(message)
                        # Uncomment below to enable Telegram alerts
                        # send_telegram(message)

            except Exception as e:
                print(f"[SCAN ERROR] {symbol}: {e}")

        time.sleep(SCAN_INTERVAL)

# ========== RUN ==========

if __name__ == "__main__":
    scan()
