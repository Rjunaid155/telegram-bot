import requests
import pandas as pd
from datetime import datetime
import os

# Telegram credentials
TELEGRAM_TOKEN = os.environ.get('TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def fetch_candles(symbol):
    url = f"https://contract.mexc.com/api/v1/contract/kline?symbol={symbol}&interval=5m&limit=50"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json().get('data', [])
            if not data:
                return None
            df = pd.DataFrame(data)
            df.columns = ['open_time', 'open', 'high', 'low', 'close', 'volume']
            df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
            df = df.astype(float)
            return df
        else:
            return None
    except:
        return None

def detect_lower_low(df):
    if len(df) < 5:
        return False
    last_lows = df['low'].iloc[-5:]
    return last_lows.iloc[-1] < last_lows.min()

def send_alert(symbol, price, tp, sl):
    message = (
        f"⚠️ [LL SCALP SHORT] {symbol}\n"
        f"Price: {price}\n"
        f"Take Profit: {tp}\n"
        f"Stop Loss: {sl}\n"
        f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
    )
    print(message)
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {'chat_id': CHAT_ID, 'text': message}
    try:
        requests.post(url, params=params)
    except Exception as e:
        print(f"Telegram Error: {e}")

def check_symbols():
    symbols_response = requests.get("https://contract.mexc.com/api/v1/contract/detail").json()
    futures_symbols = [item['symbol'] for item in symbols_response.get('data', [])]
    print(f"Fetched {len(futures_symbols)} futures symbols")

    for symbol in futures_symbols:
        df = fetch_candles(symbol)
        if df is None:
            continue

        if detect_lower_low(df):
            price = df['close'].iloc[-1]
            tp = round(price * 0.985, 4)  # 1.5%+ TP
            sl = round(price * 1.007, 4)  # tight SL
            send_alert(symbol, price, tp, sl)

if __name__ == "__main__":
    check_symbols()
