import requests
import pandas as pd
import os
import time
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get('TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {'chat_id': CHAT_ID, 'text': message}
    try:
        response = requests.post(url, params=params)
        if response.status_code != 200:
            print(f"Telegram Error: {response.text}")
    except Exception as e:
        print(f"Send Alert Error: {e}")

def fetch_candles(symbol):
    url = f"https://contract.mexc.com/api/v1/klines?symbol={symbol}&interval=5m&limit=50"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json().get('data', [])
            if not data:
                print(f"No data for {symbol}")
                return None
            df = pd.DataFrame(data, columns=['time','open','high','low','close','volume','turnover'])
            df['time'] = pd.to_datetime(df['time'], unit='ms')
            df.set_index('time', inplace=True)
            df = df.astype(float, errors='ignore')
            return df
        else:
            print(f"Fetch fail {symbol}")
            return None
    except Exception as e:
        print(f"Fetch Error for {symbol}: {e}")
        return None

def is_lower_low(df):
    recent_lows = df['low'].iloc[-5:-1]  # last 4 candles
    current_low = df['low'].iloc[-1]     # current candle
    return current_low < recent_lows.min()

def check_signals():
    symbols = ['BTC_USDT', 'ETH_USDT', 'XRP_USDT', 'DOGE_USDT', 'SOL_USDT']

    for symbol in symbols:
        df = fetch_candles(symbol)
        if df is None or len(df) < 10:
            continue

        if is_lower_low(df):
            price = df['close'].iloc[-1]
            message = f"📉 LL Alert: {symbol}\nPrice: {price}\nTime: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
            send_alert(message)
            print(f"Signal on {symbol}")
        else:
            print(f"No LL on {symbol}")
        time.sleep(0.5)  # safe delay

if __name__ == "__main__":
    check_signals()
