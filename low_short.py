import requests
import pandas as pd
import time
import telegram
import os

# Telegram Config
TELEGRAM_TOKEN = os.environ.get('TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
bot = telegram.Bot(token=TELEGRAM_TOKEN)

TIMEOUT = 10
MAX_RETRIES = 3

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

def fetch_candles(symbol, retries=MAX_RETRIES):
    url = f"https://contract.mexc.com/api/v1/contract/kline?symbol={symbol}&interval=1m&limit=10"
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                df = pd.DataFrame(data['data'], columns=["timestamp", "open", "high", "low", "close", "volume"])
                df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
                return df
            else:
                print(f"No candle data for {symbol}")
                return pd.DataFrame()
        except Exception as e:
            print(f"Fetch Error for {symbol}: {e} (attempt {attempt+1})")
            time.sleep(1)
    return pd.DataFrame()

def check_signal(symbol, df):
    if df.empty or len(df) < 3:
        return
    last = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3]

    if last['low'] < prev['low'] and prev['low'] < prev2['low']:
        wick_size = (last['high'] - last['low']) / last['low'] * 100
        if wick_size >= 1:
            msg = f" SHORT Signal\nSymbol: {symbol}\nPrice: {last['close']}\nTimeframe: 1m\nCondition: Confirmed Lower Low with Wick"
            bot.send_message(chat_id=CHAT_ID, text=msg)
            print(f"Signal Sent: {symbol}")

def scanner():
    symbols = fetch_symbols()
    print(f"Total symbols to scan: {len(symbols)}")
    while True:
        for symbol in symbols:
            df = fetch_candles(symbol)
            check_signal(symbol, df)
        time.sleep(3)

if __name__ == "__main__":
    scanner()
