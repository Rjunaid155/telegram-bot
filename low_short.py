import requests
import pandas as pd
import time
from datetime import datetime
import telegram

# Telegram Setup
bot_token = 'YOUR_TELEGRAM_BOT_TOKEN'
chat_id = 'YOUR_CHAT_ID'
bot = telegram.Bot(token=bot_token)

# Fetch Futures Symbols
def get_symbols():
    url = 'https://contract.mexc.com/api/v1/contract/detail'
    response = requests.get(url, timeout=10)
    data = response.json()
    symbols = [item['symbol'] for item in data['data']]
    return symbols

# Fetch Candle Data
def fetch_candles(symbol):
    url = f"https://contract.mexc.com/api/v1/contract/kline/{symbol}?interval=5m&limit=100"
    response = requests.get(url, timeout=10)
    data = response.json()['data']
    df = pd.DataFrame(data)
    df.columns = ['timestamp','open','high','low','close','volume']
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df.astype(float)
    return df

# Check LL Setup
def check_LL(df):
    if len(df) < 3:
        return False, None, None, None

    last_low = df['low'].iloc[-1]
    prev_low = df['low'].iloc[-2]
    prev_prev_low = df['low'].iloc[-3]

    if last_low < prev_low and prev_low < prev_prev_low:
        entry = last_low
        tp = entry * 0.985
        sl = entry * 1.005
        return True, entry, tp, sl

    return False, None, None, None

# Main Scanner
def scanner():
    symbols = get_symbols()
    print(f"Fetched {len(symbols)} futures symbols")

    while True:
        for symbol in symbols:
            try:
                df = fetch_candles(symbol)
                signal, entry, tp, sl = check_LL(df)

                if signal:
                    msg = f" LL Short Signal on {symbol}\nEntry: {entry:.4f}\nTP: {tp:.4f}\nSL: {sl:.4f}\nTime: {datetime.now().strftime('%H:%M:%S')}"
                    bot.send_message(chat_id=chat_id, text=msg)
                    print(msg)

            except Exception as e:
                print(f"Error for {symbol}: {e}")

        time.sleep(10)  # Sleep before next scan cycle

if __name__ == "__main__":
    scanner()
