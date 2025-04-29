import requests
import time
import pandas as pd
import ta
import os
import telegram

# Load env variables
MEXC_API_URL = "https://api.mexc.com"
TELEGRAM_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = telegram.Bot(token=TELEGRAM_TOKEN)

def get_all_symbols():
    url = f"{MEXC_API_URL}/api/v3/exchangeInfo"
    try:
        res = requests.get(url, timeout=10)
        symbols = [s['symbol'] for s in res.json()['symbols'] if s['quoteAsset'] == 'USDT']
        return symbols
    except Exception as e:
        print(f"Failed to fetch symbols: {e}")
        return []

def get_klines(symbol, interval='15m', limit=100):
    url = f"{MEXC_API_URL}/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        if not isinstance(data, list):
            return None
        df = pd.DataFrame(data)
        if df.shape[1] == 12:
            df.columns = [
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'num_trades',
                'taker_buy_base', 'taker_buy_quote', 'ignore'
            ]
        elif df.shape[1] == 8:
            df.columns = [
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume'
            ]
        else:
            print(f"Unexpected column count for {symbol}: {df.shape[1]}")
            return None

        df['close'] = df['close'].astype(float)
        return df
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

def analyze_rsi(symbol):
    df = get_klines(symbol)
    if df is None or df.empty:
        return

    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    latest_rsi = df['rsi'].iloc[-1]
    last_close = df['close'].iloc[-1]

    if 20 <= latest_rsi <= 25:
        suggestion = f"BUY signal for {symbol}\nPrice: {last_close}\nRSI: {latest_rsi:.2f}\nSuggested entries: {last_close*0.997:.3f} - {last_close*1.003:.3f}"
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=suggestion)
    elif 80 <= latest_rsi <= 90:
        suggestion = f"SHORT signal for {symbol}\nPrice: {last_close}\nRSI: {latest_rsi:.2f}\nSuggested entries: {last_close*1.003:.3f} - {last_close*0.997:.3f}"
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=suggestion)

def main():
    while True:
        print("Scanning...")
        symbols = get_all_symbols()
        for symbol in symbols:
            if symbol.endswith("USDT"):
                analyze_rsi(symbol)
                time.sleep(0.3)  # avoid rate limit
        print("Waiting 3 minutes...")
        time.sleep(180)  # wait before next scan

if __name__ == "__main__":
    main()
