import requests
import pandas as pd
import time
import os
from datetime import datetime

# Telegram credentials
TELEGRAM_TOKEN = os.environ.get('TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    try:
        requests.post(url, data=payload)
    except:
        pass

def fetch_symbols():
    url = "https://contract.mexc.com/api/v1/contract/ticker"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        symbols = [item['symbol'] for item in data['data'] if "_USDT" in item['symbol']]
        return symbols
    except:
        return []

def fetch_klines(symbol, interval='1m', limit=30):
    url = f"https://contract.mexc.com/api/v1/contract/kline/{symbol}?interval={interval}&limit={limit}"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        return pd.DataFrame(data['data'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    except:
        return pd.DataFrame()

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_kdj(df, n=9, k_period=3, d_period=3):
    low_min = df['low'].rolling(window=n).min()
    high_max = df['high'].rolling(window=n).max()
    rsv = (df['close'] - low_min) / (high_max - low_min) * 100

    k = rsv.ewm(com=(k_period - 1), adjust=False).mean()
    d = k.ewm(com=(d_period - 1), adjust=False).mean()
    j = 3 * k - 2 * d
    return k, d, j

def main():
    symbols = fetch_symbols()
    print(f"Fetched {len(symbols)} altcoin symbols")

    for symbol in symbols:
        df = fetch_klines(symbol)
        if df.empty:
            continue

        df['close'] = pd.to_numeric(df['close'])
        df['low'] = pd.to_numeric(df['low'])
        df['high'] = pd.to_numeric(df['high'])

        rsi = calculate_rsi(df['close'])
        k, d, j = calculate_kdj(df)

        last_rsi = rsi.iloc[-1]
        last_j = j.iloc[-1]

        if last_rsi < 35 and last_j < 20:
            message = (
                f"🔥 Scalping Alert 🔥\n\n"
                f"Symbol: {symbol}\n"
                f"RSI: {last_rsi:.2f}\n"
                f"J: {last_j:.2f}\n"
                f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
                f"Signal: Possible Short 📉"
            )
            send_telegram_message(message)

        time.sleep(0.5)

if __name__ == "__main__":
    main()
