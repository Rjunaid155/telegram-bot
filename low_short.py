import requests
import pandas as pd
import time
import telegram
import os
import threading
from queue import Queue

# Telegram Config
TELEGRAM_TOKEN = os.environ.get('TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
bot = telegram.Bot(token=TELEGRAM_TOKEN)

# Fetch Symbols
def fetch_symbols():
    url = "https://contract.mexc.com/api/v1/contract/detail"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        symbols = [item['symbol'] for item in data['data']]
        print(f"Fetched {len(symbols)} symbols")
        return symbols
    except Exception as e:
        print(f"Symbol Fetch Error: {e}")
        return []

# Fetch Candles
def fetch_candles(symbol, retries=MAX_RETRIES):
    url = f"https://contract.mexc.com/api/v1/contract/kline?symbol={symbol}&interval=1m&limit=10"
    attempt = 0
    while attempt < retries:
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                df = pd.DataFrame(data['data'], columns=['timestamp','open','high','low','close','volume','amount'])
                df[['open','high','low','close','volume','amount']] = df[['open','high','low','close','volume','amount']].astype(float)
                return df
            else:
                print(f"No candle data for {symbol}")
                return None
        except Exception as e:
            print(f"Fetch Error for {symbol}: {e} (attempt {attempt+1})")
            attempt += 1
            time.sleep(RETRY_DELAY)

    print(f"Failed to fetch data for {symbol} after {retries} attempts.")
    return None
# Signal Check
def check_signal(symbol, df):
    if df is None or len(df) < 3:
        return
    last = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3]

    # LL setup check
    if last['low'] < prev['low'] and prev['low'] < prev2['low']:
        wick_size = (last['high'] - last['low']) / last['low'] * 100
        if wick_size >= 1:  # 1% rejection wick
            msg = f"🔥 SHORT Signal 🔥\n\n📊 Symbol: {symbol}\n💰 Price: {last['close']}\n⏰ Timeframe: 1m\n✅ Condition: Confirmed Lower Low with 1% Wick"
            bot.send_message(chat_id=CHAT_ID, text=msg)
            print(f"Signal Sent: {symbol}")

# Worker Thread
def worker():
    while True:
        symbol = q.get()
        if symbol is None:
            break
        df = fetch_candles(symbol)
        check_signal(symbol, df)
        q.task_done()

# Scanner Loop
def scanner():
    symbols = fetch_symbols()
    print(f"Total symbols to scan: {len(symbols)}")

    while True:
        for symbol in symbols:
            q.put(symbol)

        q.join()  # wait for all tasks to complete

        time.sleep(3)  # delay before next scan

if __name__ == "__main__":
    q = Queue()
    num_threads = 12
    threads = []

    # Start worker threads
    for _ in range(num_threads):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)

    # Start scanning
    scanner()

    # Stop worker threads
    for _ in range(num_threads):
        q.put(None)
    for t in threads:
        t.join()
