import requests
import os
import telebot
import pandas as pd

TELEGRAM_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# RSI Calculation
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# KDJ Calculation
def calculate_kdj(df, n=14, k_period=3, d_period=3):
    low_min = df['low'].rolling(window=n).min()
    high_max = df['high'].rolling(window=n).max()
    rsv = (df['close'] - low_min) / (high_max - low_min) * 100
    k = rsv.ewm(com=(k_period-1), adjust=False).mean()
    d = k.ewm(com=(d_period-1), adjust=False).mean()
    j = 3 * k - 2 * d
    return j

# Get all Futures pairs
def get_all_futures_pairs():
    url = "https://api.bitget.com/api/mix/v1/market/contracts?productType=umcbl"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return [pair["symbol"].replace("_UMCBL", "") for pair in data["data"]]
    else:
        print("Error fetching pairs:", response.text)
        return []

# Get Candle Data
def get_candles(symbol, timeframe, limit=50):
    url = f"https://api.bitget.com/api/mix/v1/market/candles"
    params = {"symbol": f"{symbol}_UMCBL", "granularity": timeframe, "limit": limit}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()["data"]
        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume", "quoteVolume"])
        df = df.astype(float)
        return df[::-1]  # reverse order
    else:
        print(f"Error fetching candles for {symbol}:", response.text)
        return None

# Send Telegram Alert
def send_telegram_alert(message):
    bot.send_message(CHAT_ID, message)

# Check Signals and Send Alerts
def check_signals():
    pairs = get_all_futures_pairs()
    high_prob_coins = []

    for symbol in pairs:
        df_15m = get_candles(symbol, 900)
        df_1h = get_candles(symbol, 3600)

        if df_15m is None or df_1h is None:
            continue

        df_15m["rsi"] = calculate_rsi(df_15m["close"])
        df_15m["j"] = calculate_kdj(df_15m)

        df_1h["rsi"] = calculate_rsi(df_1h["close"])

        latest_15m_rsi = df_15m["rsi"].iloc[-1]
        latest_15m_j = df_15m["j"].iloc[-1]
        latest_1h_rsi = df_1h["rsi"].iloc[-1]

        # High probability conditions
        if (latest_15m_rsi <= 30 and latest_15m_j <= 20) or (latest_15m_rsi >= 70 and latest_15m_j >= 80):
            message = f"*{symbol} Signal:*\n15m RSI: {latest_15m_rsi:.2f}, J: {latest_15m_j:.2f}\n1h RSI: {latest_1h_rsi:.2f}"
            send_telegram_alert(message)
            high_prob_coins.append(symbol)

    if high_prob_coins:
        send_telegram_alert(f"High probability coins: {', '.join(high_prob_coins)}")

# Run
if __name__ == "__main__":
    check_signals()
