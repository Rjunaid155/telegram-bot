import time
import requests
import pandas as pd
import numpy as np
import ta
from telegram import Bot
import os

# Telegram setup
telegram_token = os.environ.get("TOKEN")  # Set on Render
chat_id = os.environ.get("TELEGRAM_CHAT_ID")

bot = Bot(token=telegram_token)

def send_telegram_message(message):
    bot.send_message(chat_id=chat_id, text=message)

# Function to fetch historical data from MEXC
def get_ohlcv(symbol, interval='15m', limit=100):
    url = f"https://api.mexc.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data, columns=[
        'time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'
    ])
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['close'] = df['close'].astype(float)
    return df

# Indicators
def get_rsi(df):
    rsi = ta.momentum.RSIIndicator(close=df['close'], window=14)
    return rsi.rsi().iloc[-1]

def get_atr(df):
    atr = ta.volatility.AverageTrueRange(
        high=df['high'], low=df['low'], close=df['close'], window=14)
    return atr.average_true_range().iloc[-1]

def get_sma(df):
    sma = ta.trend.SMAIndicator(close=df['close'], window=50)
    return sma.sma_indicator().iloc[-1]

def trade(symbol='BTCUSDT', interval='15m', threshold_buy=10, threshold_sell=90):
    df = get_ohlcv(symbol, interval)
    rsi = get_rsi(df)
    atr = get_atr(df)
    sma = get_sma(df)
    last_price = df['close'].iloc[-1]
    entry_price_suggestion = last_price + atr if rsi < threshold_buy else last_price - atr

    print(f"{symbol} | RSI: {rsi:.2f} | SMA: {sma:.2f} | ATR: {atr:.2f} | Last Price: {last_price:.2f}")

    # Buy signal
    if rsi < threshold_buy and last_price > sma:
        msg = f"BUY SIGNAL for {symbol} | RSI: {rsi:.2f}\nEntry: {entry_price_suggestion:.2f}"
        send_telegram_message(msg)
        print("Buy Signal Sent")

    # Sell signal
    elif rsi > threshold_sell and last_price < sma:
        msg = f"SELL SIGNAL for {symbol} | RSI: {rsi:.2f}\nEntry: {entry_price_suggestion:.2f}"
        send_telegram_message(msg)
        print("Sell Signal Sent")
    else:
        print("No signal")

# List of altcoins (MEXC supports only selected symbols)
altcoins = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ADAUSDT']  # You can expand this

def main():
    while True:
        for symbol in altcoins:
            trade(symbol, interval='15m', threshold_buy=10, threshold_sell=90)
        time.sleep(60)

if __name__ == "__main__":
    main()
