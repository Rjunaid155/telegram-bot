import requests
import pandas as pd
import ta
from datetime import datetime

import requests

def fetch_candles(symbol):
    url = f"https://api.mexc.com/api/v3/klines?symbol={symbol}&interval=5m&limit=5"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print(f"{symbol} first candle data: {data[0]}")
        print(f"Length of this candle: {len(data[0])}")
    else:
        print("Failed to fetch data.")

fetch_candles('BTCUSDT')
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
    print(message)  # for local logs
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message
    }
    try:
        response = requests.post(url, params=params)
        if response.status_code != 200:
            print(f"Failed to send Telegram message: {response.text}")
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

def check_signals():
    symbols = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT']  # apni list yahan daal
    for symbol in symbols:
        df = fetch_candles(symbol)
        if df is None or len(df) < 20:
            continue

        df['rsi'] = calculate_rsi(df['close'], 14)
        df['j'] = calculate_kdj(df, 14)

        avg_volume = df['volume'].iloc[:-1].mean()
        current_volume = df['volume'].iloc[-1]
        last_rsi = df['rsi'].iloc[-1]
        last_j = df['j'].iloc[-1]
        price = df['close'].iloc[-1]

        if last_rsi > 70 and last_j > 80:
            tp = round(price * 0.995, 4)
            sl = round(price * 1.005, 4)
            msg_type = "🔥 [SHORT SIGNAL]"

            if current_volume > 1.5 * avg_volume:
                msg_type = "🚨 [VOLUME SPIKE SHORT]"

            message = (
                f"{msg_type} {symbol}\n"
                f"📊 Price: {price}\n"
                f"RSI: {last_rsi:.2f}\n"
                f"J: {last_j:.2f}\n"
                f"Volume: {current_volume:.2f} vs Avg {avg_volume:.2f}\n"
                f"Entry: {price}\n"
                f"Take Profit: {tp}\n"
                f"Stop Loss: {sl}\n"
                f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
                f"Avoid Above: {round(price * 1.001, 4)}"
            )
            send_alert(message)

if __name__ == "__main__":
    check_signals()
