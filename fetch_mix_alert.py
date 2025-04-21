import requests
import time
import pandas as pd
import pandas_ta as ta
import datetime

# === CONFIGURATION ===
TELEGRAM_TOKEN = "<TOKEN>"
TELEGRAM_CHAT_ID = "<YOUR_TELEGRAM_CHAT_ID>"
MEXC_BASE_URL = "https://api.mexc.com"

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "OPUSDT",
    "AVAXUSDT", "MATICUSDT", "LTCUSDT", "DOTUSDT"
]

RSI_OVERBOUGHT = 85
RSI_OVERSOLD = 15

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Telegram error: {e}")

def fetch_klines(symbol, interval, limit=100):
    url = f"{MEXC_BASE_URL}/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    data = response.json()
    if not isinstance(data, list):
        raise ValueError(f"Invalid API response: {data}")
    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume", "close_time", "quote_asset_volume", "num_trades", "taker_base_vol", "taker_quote_vol", "ignore"])
    df["close"] = pd.to_numeric(df["close"], errors='coerce')
    df["open"] = pd.to_numeric(df["open"], errors='coerce')
    df["high"] = pd.to_numeric(df["high"], errors='coerce')
    df["low"] = pd.to_numeric(df["low"], errors='coerce')
    df["volume"] = pd.to_numeric(df["volume"], errors='coerce')
    df.dropna(inplace=True)
    return df

def analyze(symbol):
    try:
        df_1h = fetch_klines(symbol, "1h")
        df_4h = fetch_klines(symbol, "4h")
        df_1m = fetch_klines(symbol, "1m", limit=5)

        if df_1h.empty or df_4h.empty or df_1m.empty:
            print(f"Empty dataframe for {symbol}, skipping.")
            return

        df_1h["rsi"] = ta.rsi(df_1h["close"], length=14)
        df_4h["rsi"] = ta.rsi(df_4h["close"], length=14)
        df_1h.ta.macd(close='close', fast=12, slow=26, signal=9, append=True)

        if df_1h["rsi"].isna().all() or df_4h["rsi"].isna().all():
            print(f"RSI values NaN for {symbol}, skipping.")
            return

        rsi_1h = df_1h["rsi"].iloc[-1]
        rsi_4h = df_4h["rsi"].iloc[-1]
        macd = df_1h["MACD_12_26_9"].iloc[-1]
        macds = df_1h["MACDs_12_26_9"].iloc[-1]

        last_candle = df_1m.iloc[-1]
        candle_body = abs(last_candle["close"] - last_candle["open"])
        candle_range = last_candle["high"] - last_candle["low"]
        big_candle = (candle_body / last_candle["open"]) * 100 >= 1.0

        msg_type = None
        if rsi_1h >= RSI_OVERBOUGHT and rsi_4h >= RSI_OVERBOUGHT:
            msg_type = "Short"
        elif rsi_1h <= RSI_OVERSOLD and rsi_4h <= RSI_OVERSOLD:
            msg_type = "Long"
        elif big_candle:
            if candle_body > 0:
                msg_type = "Bonus Alert – Long Possible"
            else:
                msg_type = "Bonus Alert – Short Possible"

        if msg_type:
            time_now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            message = f"{msg_type} Signal Detected\n\n*Coin:* {symbol}\n*RSI 1h:* {rsi_1h:.2f}\n*RSI 4h:* {rsi_4h:.2f}\n*MACD:* {macd:.2f}\n*Signal:* {macds:.2f}\n*Time:* {time_now} UTC"
            send_telegram_message(message)

    except Exception as e:
        print(f"Analysis error for {symbol}: {e}")

if __name__ == "__main__":
    for coin in SYMBOLS:
        analyze(coin)
        time.sleep(1)
