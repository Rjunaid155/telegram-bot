import requests
import time
import pandas as pd
import os

TELEGRAM_TOKEN = os.getenv("TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

symbols = [
    "BTCUSDT_UMCBL", "ETHUSDT_UMCBL", "SOLUSDT_UMCBL", "XRPUSDT_UMCBL",
    "DOGEUSDT_UMCBL", "OPUSDT_UMCBL", "AVAXUSDT_UMCBL", "MATICUSDT_UMCBL",
    "LTCUSDT_UMCBL", "DOTUSDT_UMCBL"
]

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        res = requests.post(url, data=data)
        print(f"Telegram response: {res.text}")
    except Exception as e:
        print(f"Telegram error: {e}")

def fetch_bitget_candles(symbol, interval="5min", limit=50):
    url = f"https://api.bitget.com/api/v2/market/candles?symbol={symbol}&granularity={interval}&limit={limit}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Unexpected response for {symbol}: {response.text}")
            return None
        data = response.json()
        if 'data' not in data or not data['data']:
            print(f"No candle data for {symbol}")
            return None
        df = pd.DataFrame(data['data'], columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume'
        ])
        df['close'] = df['close'].astype(float)
        return df
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

def analyze_signal(symbol, df):
    if df is None or len(df) < 2:
        return None
    last_close = df['close'].iloc[-1]
    prev_close = df['close'].iloc[-2]
    move = (last_close - prev_close) / prev_close * 100
    if move > 1.5:
        return f"{symbol} Long Signal\nEntry: {last_close:.4f}\nChange: {move:.2f}%"
    elif move < -1.5:
        return f"{symbol} Short Signal\nEntry: {last_close:.4f}\nChange: {move:.2f}%"
    return None

def main():
    send_telegram_message("Signal bot is now running.")
    while True:
        for symbol in symbols:
            df = fetch_bitget_candles(symbol)
            signal = analyze_signal(symbol, df)
            if signal:
                send_telegram_message(signal)
            time.sleep(1)  # API friendly delay
        time.sleep(180)  # Wait 3 minutes

if __name__ == "__main__":
    main()
