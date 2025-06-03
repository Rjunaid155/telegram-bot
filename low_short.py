import os
import requests
import time
from datetime import datetime
import pandas as pd
import numpy as np

# Environment Variables
TELEGRAM_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# MEXC endpoints
SYMBOLS_URL = "https://contract.mexc.com/api/v1/contract/ticker"
CANDLE_URL = "https://contract.mexc.com/api/v1/contract/kline/{symbol}?interval=M5&limit=50"

# Settings
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
REJECTION_RATIO = 1.5
MAX_RETRIES = 2

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Telegram error: {e}")

def fetch_symbols():
    try:
        res = requests.get(SYMBOLS_URL, timeout=10)
        data = res.json()
        symbols = [item["symbol"] for item in data['data']]
        return symbols
    except Exception as e:
        print(f"Symbol fetch error: {e}")
        return []

def fetch_candles(symbol):
    for attempt in range(MAX_RETRIES):
        try:
            res = requests.get(CANDLE_URL.format(symbol=symbol), timeout=10)
            data = res.json()
            if 'data' in data and len(data['data']) >= RSI_PERIOD:
                return pd.DataFrame(data['data'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        except Exception as e:
            print(f"Fetch Error for {symbol}: {e} (attempt {attempt+1})")
        time.sleep(1)
    return None

def calculate_rsi(df, period=14):
    df['close'] = df['close'].astype(float)
    delta = df['close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=period).mean()
    avg_loss = pd.Series(loss).rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def check_wick_rejection(df):
    latest = df.iloc[-1]
    open_price = float(latest['open'])
    high_price = float(latest['high'])
    close_price = float(latest['close'])

    body = abs(close_price - open_price)
    upper_wick = high_price - max(open_price, close_price)

    return upper_wick >= body * REJECTION_RATIO, high_price, close_price

def scan_market():
    symbols = fetch_symbols()
    print(f"Fetched {len(symbols)} symbols")

    for symbol in symbols:
        df = fetch_candles(symbol)
        if df is None:
            continue

        wick_reject, rejection_price, current_price = check_wick_rejection(df)
        if not wick_reject:
            continue

        rsi_value = calculate_rsi(df)
        if rsi_value is None or rsi_value < RSI_OVERBOUGHT:
            continue

        message = (
            f" SHORT Signal Alert!\n"
            f"Symbol: {symbol}\n"
            f"Rejection Price: {rejection_price}\n"
            f"RSI: {round(rsi_value, 2)}\n"
            f"Current Price: {current_price}\n"
            f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )
        print(message)
        send_telegram_message(message)
        time.sleep(0.5)

if __name__ == "__main__":
    while True:
        scan_market()
        print("Waiting 30 sec before next scan...")
        time.sleep(30)
