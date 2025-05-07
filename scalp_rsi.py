import requests
import pandas as pd
import ta
from datetime import datetime
import os
import time

# Telegram credentials
TELEGRAM_TOKEN = os.environ.get('TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def fetch_candles(symbol):
    url = f"https://api.mexc.com/api/v3/klines?symbol={symbol}&interval=5m&limit=100"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if not data:
            print(f"No data for {symbol}")
            return None
        df = pd.DataFrame(data, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'num_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df.set_index('open_time', inplace=True)
        df = df.astype(float, errors='ignore')
        return df
    else:
        print(f"Failed to fetch candles for {symbol}: {response.text}")
        return None

def calculate_rsi(series, period=14):
    return ta.momentum.RSIIndicator(close=series, window=period).rsi()

def calculate_kdj(df, length=14):
    low_min = df['low'].rolling(window=length).min()
    high_max = df['high'].rolling(window=length).max()
    rsv = (df['close'] - low_min) / (high_max - low_min) * 100
    k = rsv.ewm(com=2).mean()
    d = k.ewm(com=2).mean()
    j = 3 * k - 2 * d
    return j

def send_alert(message):
    print(message)
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {'chat_id': CHAT_ID, 'text': message}
    try:
        response = requests.post(url, params=params)
        if response.status_code != 200:
            print(f"Telegram Error: {response.text}")
    except Exception as e:
        print(f"Error sending message: {e}")

def check_signals():
    # Top MEXC alts list (jitne tu chaahe daal sakta)
    symbols = [
        'BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'SOLUSDT', 'OPUSDT',
        'ORDIUSDT', 'DOGEUSDT', 'SHIBUSDT', 'LTCUSDT', 'TRXUSDT'
    ]

    for symbol in symbols:
        df = fetch_candles(symbol)
        if df is None or len(df) < 20:
            continue

        df['rsi'] = calculate_rsi(df['close'], 14)
        df['j'] = calculate_kdj(df, 14)

        last_rsi = df['rsi'].iloc[-1]
        last_j = df['j'].iloc[-1]
        price = df['close'].iloc[-1]

        print(f"{symbol} => RSI: {last_rsi:.2f}, J: {last_j:.2f}")

        # Short Signal Condition
        if last_rsi > 70 and last_j > 80:
            tp = round(price * 0.995, 4)
            sl = round(price * 1.005, 4)

            message = (
                f"🔥 [SHORT SIGNAL] {symbol}\n"
                f"📊 Price: {price}\n"
                f"RSI: {last_rsi:.2f}\n"
                f"J: {last_j:.2f}\n"
                f"Entry: {price}\n"
                f"Take Profit: {tp}\n"
                f"Stop Loss: {sl}\n"
                f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
            )
            send_alert(message)

if __name__ == "__main__":
    while True:
        check_signals()
        print("Waiting for next scan...\n")
        time.sleep(60)  # check every 60 sec
