import os
import requests
import time
import pandas as pd
import pandas_ta as ta
import datetime

# === CONFIGURATION ===
TELEGRAM_TOKEN = os.getenv("TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
MEXC_BASE_URL = "https://api.mexc.com"

RSI_OVERBOUGHT = 85
RSI_OVERSOLD = 15

# === SYMBOL FETCHING ===
def fetch_all_symbols():
    try:
        url = f"{MEXC_BASE_URL}/api/v3/exchangeInfo"
        response = requests.get(url)
        data = response.json()
        return [s["symbol"] for s in data["symbols"] if s["quoteAsset"] == "USDT" and s["status"] == "TRADING"]
    except Exception as e:
        print("Symbol fetch error:", e)
        return []
    
# === TELEGRAM MESSAGE ===
def send_telegram_message(message):
    try:
        if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
            print("Missing Telegram credentials.")
            return
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, data=payload)
        print("Telegram response:", response.text)
    except Exception as e:
        print("Telegram error:", e)

# === KLINES ===
def fetch_klines(symbol, interval, limit=100):
    try:
        url = f"{MEXC_BASE_URL}/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
        response = requests.get(url)
        data = response.json()
        df = pd.DataFrame(data, columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "num_trades", "taker_base_vol", "taker_quote_vol", "ignore"
        ])
        df["close"] = pd.to_numeric(df["close"])
        df["open"] = pd.to_numeric(df["open"])
        df["high"] = pd.to_numeric(df["high"])
        df["low"] = pd.to_numeric(df["low"])
        df["volume"] = pd.to_numeric(df["volume"])
        return df
    except Exception as e:
        print(f"Kline fetch error for {symbol}:", e)
        return pd.DataFrame()

# === ANALYSIS ===
def analyze(symbol):
    try:
        df_1h = fetch_klines(symbol, "1h")
        df_4h = fetch_klines(symbol, "4h")
        df_1m = fetch_klines(symbol, "1m", limit=5)

        if df_1h.empty or df_4h.empty or df_1m.empty:
            return

        df_1h["rsi"] = ta.rsi(df_1h["close"], length=14)
        df_4h["rsi"] = ta.rsi(df_4h["close"], length=14)
        df_1h.ta.macd(close='close', fast=12, slow=26, signal=9, append=True)

        rsi_1h = df_1h["rsi"].iloc[-1]
        rsi_4h = df_4h["rsi"].iloc[-1]
        macd = df_1h["MACD_12_26_9"].iloc[-1]
        macds = df_1h["MACDs_12_26_9"].iloc[-1]

        # 1-minute spike candle check
        last_candle = df_1m.iloc[-1]
        candle_body = abs(last_candle["close"] - last_candle["open"])
        big_candle = (candle_body / last_candle["open"]) * 100 >= 1.0

        msg_type = None
        if rsi_1h >= RSI_OVERBOUGHT and rsi_4h >= RSI_OVERBOUGHT:
            msg_type = "Short Signal"
        elif rsi_1h <= RSI_OVERSOLD and rsi_4h <= RSI_OVERSOLD:
            msg_type = "Long Signal"
        elif big_candle:
            if last_candle["close"] > last_candle["open"]:
                msg_type = "Bonus Spike – Long Possible"
            else:
                msg_type = "Bonus Spike – Short Possible"

        if msg_type:
            time_now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            message = f"{msg_type} Detected\n\n*Coin:* {symbol}\n*RSI 1h:* {rsi_1h:.2f}\n*RSI 4h:* {rsi_4h:.2f}\n*MACD:* {macd:.2f}\n*Signal:* {macds:.2f}\n*Time:* {time_now} UTC"
            send_telegram_message(message)

    except Exception as e:
        print(f"Analysis error for {symbol}:", e)

# === MAIN ===
def main():
    print("Bot started...")
    send_telegram_message("Signal bot is now running.")
    symbols = fetch_all_symbols()

    for symbol in symbols:
        if symbol.endswith("USDT"):
            analyze(symbol)
            time.sleep(0.5)  # To avoid rate limits

if __name__ == "__main__":
    main()
