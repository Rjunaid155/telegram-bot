import requests
import pandas as pd
import ta
from datetime import datetime
import time
import os

# Telegram credentials from environment
TELEGRAM_TOKEN = os.environ.get('TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# MEXC Futures symbols fetch
def get_symbols():
    url = 'https://contract.mexc.com/api/v1/contract/ticker'
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        symbols = [item['symbol'] for item in data['data']]
        return symbols
    except:
        return []

# Candle data fetch
def fetch_candles(symbol):
    url = f"https://contract.mexc.com/api/v1/contract/kline?symbol={symbol}&interval=5m&limit=50"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if not data['data']:
            return None
        df = pd.DataFrame(data['data'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        df = df.astype(float)
        return df
    except:
        return None

# RSI calculation
def calculate_rsi(series, period=14):
    return ta.momentum.RSIIndicator(close=series, window=period).rsi()

# Lower Low detection
def is_lower_low(df):
    if len(df) < 5:
        return False
    lows = df['low'].iloc[-5:]
    return lows.iloc[-1] < min(lows.iloc[:-1])

# Alert send
def send_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {'chat_id': CHAT_ID, 'text': message}
    try:
        requests.post(url, params=params, timeout=5)
    except:
        pass

# Main scanner
def check_signals():
    symbols = get_symbols()
    print(f"Fetched {len(symbols)} futures symbols")

    for symbol in symbols:
        df = fetch_candles(symbol)
        if df is None or len(df) < 20:
            continue

        df['rsi'] = calculate_rsi(df['close'])

        # LL condition
        if is_lower_low(df):
            last_rsi = df['rsi'].iloc[-1]
            price = df['close'].iloc[-1]
            tp = round(price * 0.985, 4)  # 1.5% TP
            sl = round(price * 1.01, 4)

            message = (
                f" [SHORT SIGNAL] {symbol}\n"
                f"Price: {price}\n"
                f"RSI: {last_rsi:.2f}\n"
                f"Lower Low Detected \n"
                f"Entry: {price}\n"
                f"Take Profit: {tp}\n"
                f"Stop Loss: {sl}\n"
                f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
            )
            send_alert(message)

        time.sleep(0.1)  # 100ms delay to avoid timeout

if __name__ == "__main__":
    while True:
        check_signals()
