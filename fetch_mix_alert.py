import requests
import pandas as pd
import time
import os

TELEGRAM_TOKEN = os.getenv('TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

SYMBOLS = [
    'BTCUSDT_UMCBL', 'ETHUSDT_UMCBL', 'SOLUSDT_UMCBL', 'XRPUSDT_UMCBL',
    'AVAXUSDT_UMCBL', 'DOGEUSDT_UMCBL', 'OPUSDT_UMCBL', 'LTCUSDT_UMCBL',
    'MATICUSDT_UMCBL', 'DOTUSDT_UMCBL'
]

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message
    }
    response = requests.post(url, data=payload)
    print("Telegram response:", response.text)

def fetch_bitget_candles(symbol, interval="5min", limit=100):
    url = f"https://api.bitget.com/api/v2/market/candles?symbol={symbol}&granularity={interval}&limit={limit}"
    try:
        response = requests.get(url)
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

def analyze_symbol(symbol):
    df = fetch_bitget_candles(symbol)
    if df is None or df.empty or 'close' not in df.columns:
        print(f"Skipping {symbol} due to missing data.")
        return

    last = df['close'].iloc[-1]
    prev = df['close'].iloc[-2]
    change_pct = ((last - prev) / prev) * 100

    if abs(change_pct) > 1.2:
        direction = "LONG" if change_pct > 0 else "SHORT"
        msg = f"{symbol.replace('_UMCBL', '')} | {direction} | Move: {change_pct:.2f}% | Entry: {last}"
        send_telegram_alert(msg)

def main():
    send_telegram_alert("Signal bot is now running.")
    while True:
        for symbol in SYMBOLS:
            analyze_symbol(symbol)
        time.sleep(180)  # check every 3 mins

if __name__ == "__main__":
    main()
