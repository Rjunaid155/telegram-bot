import ccxt
import pandas as pd
import pandas_ta as ta
import requests
from datetime import datetime
import os
# Telegram config
TELEGRAM_TOKEN = 'TOKEN'
CHAT_ID = 'TELEGRAM_CHAT_ID'

# MEXC Exchange
exchange = ccxt.mexc()

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'CHAT_ID': CHAT_ID, 'text': message}
    requests.post(url, data=payload)

def fetch_ohlcv(pair, timeframe='15m', limit=50):
    try:
        data = exchange.fetch_ohlcv(pair, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(data, columns=['time','open','high','low','close','volume'])
        return df
    except Exception as e:
        print(f"Error fetching {pair}: {str(e)}")
        return None

def check_simple_signals():
    markets = exchange.load_markets()
    PAIR_LIST = [symbol for symbol in markets if 'USDT' in symbol and '/USDT' in symbol]

    found_pairs = []

    for pair in PAIR_LIST:
        df_15m = fetch_ohlcv(pair, '15m')
        if df_15m is None or len(df_15m) < 30:
            continue

        df_15m['rsi'] = ta.rsi(df_15m['close'], length=14)
        kdj_15m = ta.stoch(df_15m['high'], df_15m['low'], df_15m['close'])
        df_15m['K'] = kdj_15m['STOCHk_14_3_3']
        df_15m['D'] = kdj_15m['STOCHd_14_3_3']
        df_15m['J'] = 3 * df_15m['K'] - 2 * df_15m['D']

        latest = df_15m.iloc[-1]

        # Easy condition: RSI <= 50 and J <= 50
        if latest['rsi'] <= 50 and latest['J'] <= 50:
            print(f"{pair} -> RSI: {latest['rsi']:.2f}, J: {latest['J']:.2f}")
            found_pairs.append(pair)

    if found_pairs:
        message = f"🟢 Signal Coins (Easy Mode)\n\n"
        for p in found_pairs:
            message += f"- {p}\n"
        message += f"\nTime: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"

        print(message)
        send_telegram(message)
    else:
        print("No signals found.")

# Run simple scanner
check_simple_signals()
