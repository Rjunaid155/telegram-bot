import requests
import pandas as pd
import time
import telegram
import os

# Telegram Config
TELEGRAM_TOKEN = os.environ.get('TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# Fetch Symbols
def fetch_symbols():
    url = "https://contract.mexc.com/api/v1/contract/ticker"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    symbols = [item['symbol'] for item in data['data'] if '_USDT' in item['symbol']]
    return symbols

# Fetch Candles
def fetch_candles(symbol):
    url = f"https://contract.mexc.com/api/v1/contract/kline/{symbol}?interval=5m&limit=30"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()['data']
        df = pd.DataFrame(data)
        df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        return df
    except Exception as e:
        print(f"Fetch Error for {symbol}: {e}")
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
            msg = f" SHORT Signal \nSymbol: {symbol}\nPrice: {last['close']}\nTimeframe: 5m\nCondition: Confirmed Lower Low with Wick"
            bot.send_message(chat_id=chat_id, text=msg)
            print(f"Signal Sent: {symbol}")

# Scanner Loop
def scanner():
    symbols = fetch_symbols()
    print(f"Fetched {len(symbols)} symbols")
    while True:
        for symbol in symbols:
            df = fetch_candles(symbol)
            check_signal(symbol, df)
        time.sleep(3)  # adjust as needed

if __name__ == "__main__":
    scanner()
