import requests
import pandas as pd
import os
from datetime import datetime

# Telegram credentials
TELEGRAM_TOKEN = os.environ.get('TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# Fetch futures symbols
def fetch_futures_symbols():
    url = "https://contract.mexc.com/api/v1/contract/detail"
    response = requests.get(url)
    data = response.json()
    symbols = [item['symbol'] for item in data['data']]
    return symbols

# Fetch candles
def fetch_candles(symbol, interval='5m'):
    url = f"https://contract.mexc.com/api/v1/contract/kline?symbol={symbol}&interval={interval}&limit=50"
    response = requests.get(url, timeout=10)
    data = response.json()
    if 'data' not in data or not data['data']:
        return None
    df = pd.DataFrame(data['data'])
    df.columns = ['time', 'open', 'high', 'low', 'close', 'volume', 'amount']
    df = df.astype(float)
    return df

# Send telegram alert
def send_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {'chat_id': CHAT_ID, 'text': message}
    try:
        requests.post(url, params=params)
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

# Check LL signals
def check_signals():
    symbols = fetch_futures_symbols()
    print(f"Fetched {len(symbols)} future symbols")

    for symbol in symbols:
        df = fetch_candles(symbol)
        if df is None or len(df) < 5:
            continue

        lows = df['low']
        # LL pattern: current low < previous low and previous low < one before that
        if lows.iloc[-1] < lows.iloc[-2] and lows.iloc[-2] < lows.iloc[-3]:
            price = df['close'].iloc[-1]
            tp = round(price * 0.985, 4)
            sl = round(price * 1.005, 4)

            message = (
                f" [LL SHORT] {symbol}\n"
                f" Price: {price}\n"
                f" Lower Low Detected\n"
                f" Entry: {price}\n"
                f"Take Profit: {tp}\n"
                f"Stop Loss: {sl}\n"
                f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
            )
            print(message)
            send_alert(message)

if __name__ == "__main__":
    check_signals()
