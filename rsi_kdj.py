import os
import time
import requests
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.momentum import StochasticOscillator
import telegram

# Environment variables
TELEGRAM_TOKEN = os.getenv("TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = telegram.Bot(token=TELEGRAM_TOKEN)

MEXC_BASE_URL = "https://api.mexc.com"


def get_all_usdt_symbols():
    url = f"{MEXC_BASE_URL}/api/v3/exchangeInfo"
    resp = requests.get(url)
    data = resp.json()
    symbols = [s['symbol'] for s in data['symbols'] if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING']
    return symbols


def get_klines(symbol, interval='15m', limit=100):
    url = f"{MEXC_BASE_URL}/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    return df


def calculate_indicators(df):
    df['rsi'] = RSIIndicator(close=df['close'], window=14).rsi()
    kdj = StochasticOscillator(high=df['high'], low=df['low'], close=df['close'], window=14, smooth_window=3)
    df['kdj_k'] = kdj.stoch()
    df['kdj_d'] = kdj.stoch_signal()
    df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']
    return df


def check_volume_spike(df):
    avg_vol = df['volume'][:-1].tail(10).mean()
    last_vol = df['volume'].iloc[-1]
    return last_vol > 1.5 * avg_vol


def analyze(symbol):
    try:
        df = get_klines(symbol)
        df = calculate_indicators(df)

        rsi = df['rsi'].iloc[-1]
        j_line = df['kdj_j'].iloc[-1]
        volume_spike = check_volume_spike(df)
        price = df['close'].iloc[-1]

        signal = None
        if rsi >= 80 and j_line >= 80:
            signal = "Strong SHORT"
        elif rsi <= 20 and j_line <= 20:
            signal = "Strong LONG"

        if signal and volume_spike:
            entry_range = f"Entry Range: {round(price*0.995, 4)} - {round(price*1.005, 4)}"
            tp = round(price * (0.985 if signal == "Strong SHORT" else 1.015), 4)
            sl = round(price * (1.015 if signal == "Strong SHORT" else 0.985), 4)

            msg = (
                f"{signal} Signal Detected for {symbol}\n"
                f"Price: {price}\n{entry_range}\nTP: {tp} | SL: {sl}\n"
                f"RSI: {round(rsi,2)} | KDJ-J: {round(j_line,2)}"
            )
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")


def main():
    while True:
        print("Scanning...")
        symbols = get_all_usdt_symbols()
        for symbol in symbols:
            time.sleep(0.6)  # Prevent rate limit
            analyze(symbol)
        print("Scan complete. Sleeping 3 minutes...")
        time.sleep(180)


if __name__ == "__main__":
    main()
