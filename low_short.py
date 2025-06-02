import requests
import pandas as pd
import time
import telegram
import os

# Telegram config
TELEGRAM_TOKEN = os.environ.get('TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
bot = telegram.Bot(token=TELEGRAM_TOKEN)

# Config
MAX_RETRIES = 3
TIMEOUT = 10

# Fetch Symbols
def fetch_symbols():
    url = "https://contract.mexc.com/api/v1/contract/detail"
    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        symbols = [item['symbol'] for item in data['data']]
        print(f"Fetched {len(symbols)} symbols")
        return symbols
    except Exception as e:
        print(f"Symbol Fetch Error: {e}")
        return []

# Fetch Candles with retries
def fetch_candles(symbol, retries=MAX_RETRIES):
    url = f"https://contract.mexc.com/api/v1/contract/kline?symbol={symbol}&interval=1m&limit=10"
    attempt = 0
    while attempt < retries:
        try:
            response = requests.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                df = pd.DataFrame(data['data'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
                return df
            else:
                return None
        except Exception as e:
            attempt += 1
            print(f"Fetch Error for {symbol}: {e} (attempt {attempt})")
            time.sleep(1)
    return None

# Signal Check
def check_signal(symbol, df):
    if df is None or len(df) < 3:
        return
    last = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3]

    if last['low'] < prev['low'] and prev['low'] < prev2['low']:
        wick_size = (last['high'] - last['low']) / last['low'] * 100
        if wick_size >= 1:
            msg = f"🚨 SHORT Signal 🚨\n\nSymbol: {symbol}\nPrice: {last['close']}\nTimeframe: 1m\nCondition: Confirmed Lower Low with 1% Rejection Wick"
            bot.send_message(chat_id=CHAT_ID, text=msg)
            print(f"Signal Sent: {symbol}")

# Scanner Loop
def scanner():
    symbols = fetch_symbols()
    print(f"Total symbols to scan: {len(symbols)}")
    while True:
        for symbol in symbols:
            df = fetch_candles(symbol)
            check_signal(symbol, df)
        time.sleep(2)

if __name__ == "__main__":
    scanner()
