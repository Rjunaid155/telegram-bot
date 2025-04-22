import requests
import time
import pandas as pd
import pandas_ta as ta
import datetime
import os

TELEGRAM_TOKEN = os.getenv("TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    print("Missing Telegram credentials.")
    exit()

MEXC_BASE_URL = "https://api.mexc.com"

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT",
    "OPUSDT", "AVAXUSDT", "MATICUSDT", "LTCUSDT", "DOTUSDT"
]

RSI_OVERBOUGHT = 80
RSI_OVERSOLD = 20

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, data=payload)
        print("Telegram response:", response.text)
    except Exception as e:
        print(f"Telegram error: {e}")

def fetch_klines(symbol, interval, limit=100):
    url = f"{MEXC_BASE_URL}/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data, columns=[
        "timestamp", "open", "high", "low", "close", "volume", "close_time",
        "quote_asset_volume", "num_trades", "taker_base_vol", "taker_quote_vol", "ignore"
    ])
    df["close"] = pd.to_numeric(df["close"])
    df["high"] = pd.to_numeric(df["high"])
    df["low"] = pd.to_numeric(df["low"])
    df["open"] = pd.to_numeric(df["open"])
    df["volume"] = pd.to_numeric(df["volume"])
    return df

def analyze(symbol):
    try:
        df_1h = fetch_klines(symbol, "1h")
        df_4h = fetch_klines(symbol, "4h")
        df_1m = fetch_klines(symbol, "1m", limit=5)

        df_1h["rsi"] = ta.rsi(df_1h["close"], length=14)
        df_4h["rsi"] = ta.rsi(df_4h["close"], length=14)
        df_1h.ta.macd(close='close', fast=12, slow=26, signal=9, append=True)

        rsi_1h = df_1h["rsi"].iloc[-1]
        rsi_4h = df_4h["rsi"].iloc[-1]
        macd = df_1h["MACD_12_26_9"].iloc[-1]
        macds = df_1h["MACDs_12_26_9"].iloc[-1]

        last_candle = df_1m.iloc[-1]
        candle_body = abs(last_candle["close"] - last_candle["open"])
        candle_range = last_candle["high"] - last_candle["low"]
        big_candle = (candle_body / last_candle["open"]) * 100 >= 0.6  # 0.6% movement

        print(f"\n[{symbol}]")
        print(f"RSI 1h: {rsi_1h:.2f}, RSI 4h: {rsi_4h:.2f}, MACD: {macd:.2f}, MACDs: {macds:.2f}, Big Candle: {big_candle}")

        msg_type = None
        if rsi_1h >= RSI_OVERBOUGHT and rsi_4h >= RSI_OVERBOUGHT:
            msg_type = "Short Signal"
        elif rsi_1h <= RSI_OVERSOLD and rsi_4h <= RSI_OVERSOLD:
            msg_type = "Long Signal"
        elif big_candle:
            if candle_body > 0:
                msg_type = "Spike Alert – Long Possible"
            else:
                msg_type = "Spike Alert – Short Possible"

        if msg_type:
            time_now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            message = f"{msg_type}\n\n*Coin:* {symbol}\n*RSI 1h:* {rsi_1h:.2f}\n*RSI 4h:* {rsi_4h:.2f}\n*MACD:* {macd:.2f}\n*Signal:* {macds:.2f}\n*Time:* {time_now} UTC"
            send_telegram_message(message)
        else:
            print(f"No signal for {symbol}")
    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")

# === RUN ===
print("Signal bot is now running.")
for coin in SYMBOLS:
    analyze(coin)
    time.sleep(1)
