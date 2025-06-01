import requests
import pandas as pd
import ta
import os
import time
from datetime import datetime

# Telegram Config
TELEGRAM_TOKEN = os.environ.get('TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# Candles fetch function
def fetch_candles(symbol):
    try:
        url = f"https://contract.mexc.com/api/v1/klines?symbol={symbol}&interval=5m&limit=100"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()['data']
        if not data:
            return None
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        df = df.astype(float)
        return df
    except Exception as e:
        print(f"Fetch Error for {symbol}: {e}")
        return None

# Lower Low detection function
def is_lower_low(df):
    lows = df['low']
    if len(lows) < 3:
        return False
    if lows.iloc[-1] < lows.iloc[-2] < lows.iloc[-3]:
        return True
    return False

# Send Telegram alert
def send_alert(symbol, price, tp, sl):
    message = (
        f" [SHORT SIGNAL] {symbol}\n"
        f" Price: {price}\n"
        f"Take Profit: {tp}\n"
        f"Stop Loss: {sl}\n"
        f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
    )
    print(message)
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {
        'chat_id': CHAT_ID,
        'text': message
    }
    try:
        requests.post(url, params=params)
    except Exception as e:
        print(f"Telegram Error: {e}")

# All futures symbols fetch
def get_symbols():
    try:
        url = "https://contract.mexc.com/api/v1/contract/detail"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()['data']
        symbols = [item['symbol'] for item in data]
        print(f"Fetched {len(symbols)} future symbols")
        return symbols
    except Exception as e:
        print(f"Error fetching symbols: {e}")
        return []

# Main Scanner
def check_signals():
    symbols = get_symbols()
    for symbol in symbols:
        df = fetch_candles(symbol)
        if df is None:
            continue
        if is_lower_low(df):
            price = df['close'].iloc[-1]
            tp = round(price * 0.985, 4)  # 1.5% TP
            sl = round(price * 1.005, 4)
            send_alert(symbol, price, tp, sl)
        time.sleep(0.3)

# Continuous Scanner Loop
if __name__ == "__main__":
    while True:
        check_signals()
        print("Scan completed. Waiting 20 seconds for next scan...\n")
        time.sleep(20)
