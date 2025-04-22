import requests
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import time

# === TELEGRAM CONFIGURATION ===
TELEGRAM_TOKEN = ("TOKEN")
CHAT_ID = ("TELEGRAM_CHAT_ID")

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")

# === BITGET API CONFIG ===
BITGET_API_URL = "https://api.bitget.com/api/v2/market/candles"
ALL_SYMBOLS_URL = "https://api.bitget.com/api/v2/market/tickers?productType=umcbl"

def get_all_futures_symbols():
    try:
        response = requests.get(ALL_SYMBOLS_URL)
        print("Raw response:", response.text)  # Debug ke liye
        data = response.json()
        symbols = [item["symbol"] for item in data["data"]]
        return symbols
    except Exception as e:
        print("Symbol fetch error:", e)
        return []
def fetch_klines(symbol: str, interval: str, limit=100):
    try:
        params = {
            "symbol": symbol,
            "granularity": interval,
            "limit": limit
        }
        res = requests.get(BITGET_API_URL, params=params).json()
        if "data" in res:
            df = pd.DataFrame(res['data'], columns=[
                "timestamp", "open", "high", "low", "close", "volume", "turnover"
            ])
            df["close"] = df["close"].astype(float)
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit='ms')
            return df[::-1].reset_index(drop=True)
        return pd.DataFrame()
    except Exception as e:
        print(f"Error fetching {symbol} - {e}")
        return pd.DataFrame()

def analyze_symbol(symbol):
    try:
        df_1h = fetch_klines(symbol, "1H")
        df_4h = fetch_klines(symbol, "4H")
        df_3m = fetch_klines(symbol, "3m")

        if df_1h.empty or df_4h.empty or df_3m.empty:
            return

        df_1h['rsi'] = ta.rsi(df_1h['close'], length=14)
        macd_1h = ta.macd(df_1h['close'])
        df_1h = pd.concat([df_1h, macd_1h], axis=1)

        macd_4h = ta.macd(df_4h['close'])
        df_4h = pd.concat([df_4h, macd_4h], axis=1)

        rsi = round(df_1h['rsi'].iloc[-1], 2)
        macd_trend_1h = "Bullish" if df_1h['MACD_12_26_9'].iloc[-1] > 0 else "Bearish"
        macd_trend_4h = "Bullish" if df_4h['MACD_12_26_9'].iloc[-1] > 0 else "Bearish"

        # === LONG/SHORT ALERT ===
        if rsi < 20 and macd_trend_1h == "Bullish":
            msg = f"[ALERT] LONG: {symbol}\nRSI (1H): {rsi} | MACD: {macd_trend_1h}\nEntry Soon - Big Bounce Expected"
            print(msg + "\n")
            send_telegram_alert(msg)

        elif rsi > 80 and macd_trend_4h == "Bearish":
            msg = f"[ALERT] SHORT: {symbol}\nRSI (4H): {rsi} | MACD: {macd_trend_4h}\nHeavy Resistance Zone"
            print(msg + "\n")
            send_telegram_alert(msg)

        # === BONUS SPIKE ALERT ===
        last_candle = df_3m.iloc[-1]
        body = abs(float(last_candle['close']) - float(last_candle['open']))
        wick = float(last_candle['high']) - float(last_candle['low'])

        if wick != 0 and body / wick > 0.7:
            msg = f"[BONUS ALERT] {symbol}\nCandle Spike Detected in 3m TF\nPotential Big Move Incoming!"
            print(msg + "\n")
            send_telegram_alert(msg)

    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")

def main():
    symbols = get_all_futures_symbols()
    for symbol in symbols:
        analyze_symbol(symbol)
        time.sleep(0.8)  # Respect API rate limits

if __name__ == "__main__":
    main()
