import requests
import pandas as pd
import ta
from datetime import datetime
import os

# Telegram credentials (Render environment variables)
TELEGRAM_TOKEN = os.environ.get('TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# Fetch candles from MEXC (5m TF)
def fetch_candles(symbol):
    url = f"https://contract.mexc.com/api/v1/klines?symbol={symbol}&interval=5m&limit=100"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json().get('data')
        if not data:
            print(f"Skipping {symbol}: No candle data")
            return None
        df = pd.DataFrame(data, columns=['open_time', 'open', 'high', 'low', 'close', 'volume'])
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df.set_index('open_time', inplace=True)
        df = df.astype(float, errors='ignore')
        return df
    else:
        print(f"Failed to fetch candles for {symbol}")
        return None
# RSI calculation
def calculate_rsi(series, period=14):
    return ta.momentum.RSIIndicator(close=series, window=period).rsi()

# KDJ J-line calculation
def calculate_kdj(df, length=14):
    low_min = df['low'].rolling(window=length).min()
    high_max = df['high'].rolling(window=length).max()
    rsv = (df['close'] - low_min) / (high_max - low_min) * 100
    k = rsv.ewm(com=2).mean()
    d = k.ewm(com=2).mean()
    j = 3 * k - 2 * d
    return j

# Send Telegram alert
def send_alert(message):
    print(message)  # local logs
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {
        'chat_id': CHAT_ID,
        'text': message
    }
    try:
        response = requests.post(url, params=params)
        if response.status_code != 200:
            print(f"Failed to send Telegram message: {response.text}")
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

# Signal check logic
def check_signals():
    symbols_url = "https://api.mexc.com/api/v3/exchangeInfo"
    response = requests.get(symbols_url)
    if response.status_code != 200:
        print("Failed to fetch symbol list")
        return

    all_symbols = [s['symbol'] for s in response.json()['symbols'] if 'USDT' in s['symbol']]
    print(f"Total symbols fetched: {len(all_symbols)}")

    for symbol in all_symbols:
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

        print(f"{symbol} => RSI: {last_rsi:.2f}, J: {last_j:.2f}, Volume: {current_volume:.2f}, Avg: {avg_volume:.2f}")

        if last_rsi >= 80 and last_j > 90:
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
                f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
            )
            send_alert(message)

if __name__ == "__main__":
    while True:
        check_signals()
