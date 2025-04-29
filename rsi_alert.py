import time
import pandas as pd
import numpy as np
from binance.client import Client
import talib
from telegram import Bot

# Binance API keys
api_key = 'YOUR_API_KEY'
api_secret = 'YOUR_API_SECRET'

# Telegram Bot token and chat ID
telegram_token = 'TOKEN'
chat_id = 'TELEGRAM_CHAT_ID'

client = Client(api_key, api_secret)
bot = Bot(token=telegram_token)

# Function to send message on Telegram
def send_telegram_message(message):
    bot.send_message(chat_id=chat_id, text=message)

# ATR Calculation function
def get_atr(symbol, interval='15m', lookback=100):
    bars = client.get_klines(symbol=symbol, interval=interval, limit=lookback)
    data = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    data['high'] = data['high'].astype(float)
    data['low'] = data['low'].astype(float)
    data['close'] = data['close'].astype(float)
    
    atr = talib.ATR(data['high'], data['low'], data['close'], timeperiod=14)
    return atr[-1]

# RSI Calculation function
def get_rsi(symbol, interval='15m', lookback=100):
    bars = client.get_klines(symbol=symbol, interval=interval, limit=lookback)
    data = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    data['close'] = data['close'].astype(float)
    rsi = talib.RSI(data['close'], timeperiod=14)
    return rsi[-1]

# SMA Calculation function
def get_sma(symbol, interval='15m', lookback=100):
    bars = client.get_klines(symbol=symbol, interval=interval, limit=lookback)
    data = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    data['close'] = data['close'].astype(float)
    
    sma = talib.SMA(data['close'], timeperiod=50)
    return sma[-1]  # 50-period SMA

# Trading logic based on RSI, ATR, and SMA
def trade(symbol='BTCUSDT', threshold_buy=10, threshold_sell=90, interval='15m'):
    rsi = get_rsi(symbol, interval)
    atr = get_atr(symbol, interval)
    sma = get_sma(symbol, interval)
    
    print(f"Current RSI for {symbol} ({interval}): {rsi}")
    print(f"Current ATR for {symbol} ({interval}): {atr}")
    print(f"Current SMA for {symbol} ({interval}): {sma}")
    
    # Entry price suggestion based on ATR
    bars = client.get_klines(symbol=symbol, interval=interval, limit=1)
    last_price = float(bars[-1][4])  # Last closing price
    entry_price_suggestion = last_price + atr if rsi < threshold_buy else last_price - atr
    
    print(f"Suggested Entry Price for {symbol}: {entry_price_suggestion}")
    
    # Bullish or Bearish trend check based on SMA
    if last_price > sma:  # Bullish trend
        print("Market is in Bullish Trend")
    else:  # Bearish trend
        print("Market is in Bearish Trend")
    
    # Buy condition (RSI and trend check)
    if rsi < threshold_buy and last_price > sma:
        message = f"RSI below 10. Oversold condition. Buy Signal for {symbol}!\nSuggested Entry Price: {entry_price_suggestion}"
        send_telegram_message(message)
        print("Buy Signal Sent to Telegram")
    
    # Sell condition (RSI and trend check)
    elif rsi > threshold_sell and last_price < sma:
        message = f"RSI above 90. Overbought condition. Sell Signal for {symbol}!\nSuggested Entry Price: {entry_price_suggestion}"
        send_telegram_message(message)
        print("Sell Signal Sent to Telegram")
    else:
        print("No action. RSI is between thresholds or trend is not favorable.")

# Function to get a list of altcoins
def get_altcoins():
    exchange_info = client.get_exchange_info()
    symbols = exchange_info['symbols']
    altcoins = []
    for symbol in symbols:
        if symbol['status'] == 'TRADING' and 'USDT' in symbol['symbol']:  # Filter for USDT pairs
            altcoins.append(symbol['symbol'])
    return altcoins

# Main function to run the bot for both timeframes and all altcoins
def main():
    altcoins = get_altcoins()  # Get list of altcoins
    while True:
        for symbol in altcoins:
            # Run for 15-minute interval
            trade(symbol, interval='15m', threshold_buy=5, threshold_sell=95)
            
            # Run for 1-hour interval
            trade(symbol, interval='1h', threshold_buy=5, threshold_sell=95)
        
        time.sleep(60)  # Run every minute

# Execute the main function
if __name__ == "__main__":
    main()
