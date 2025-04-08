import requests
import time
import os
from datetime import datetime

# Load from environment variables
TELEGRAM_TOKEN = os.getenv("TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Settings
INTERVAL = '5m'
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "MATICUSDT"]
RSI_PERIOD = 14
ATR_PERIOD = 14
VOLUME_MULTIPLIER = 2
ATR_BODY_MULTIPLIER = 1.5
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30


def get_klines(symbol, interval, limit=100):
    url = f"https://api.mexc.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        response = requests.get(url)
        data = response.json()
        return data
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return []


def calculate_rsi(closes):
    gains = []
    losses = []
    for i in range(1, len(closes)):
        delta = closes[i] - closes[i - 1]
        if delta >= 0:
            gains.append(delta)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(delta))
    avg_gain = sum(gains[-RSI_PERIOD:]) / RSI_PERIOD
    avg_loss = sum(losses[-RSI_PERIOD:]) / RSI_PERIOD
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_atr(klines):
    trs = []
    for i in range(1, len(klines)):
        high = float(klines[i][2])
        low = float(klines[i][3])
        prev_close = float(klines[i - 1][4])
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)
    atr = sum(trs[-ATR_PERIOD:]) / ATR_PERIOD
    return atr


def send_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    requests.post(url, json=payload)


def check_signals():
    for symbol in SYMBOLS:
        klines = get_klines(symbol, INTERVAL)
        if len(klines) < 20:
            continue

        close_prices = [float(k[4]) for k in klines]
        volumes = [float(k[5]) for k in klines]
        opens = [float(k[1]) for k in klines]
        highs = [float(k[2]) for k in klines]
        lows = [float(k[3]) for k in klines]

        rsi = calculate_rsi(close_prices)
        atr = calculate_atr(klines)

        vol_spike = volumes[-1] > VOLUME_MULTIPLIER * sum(volumes[-21:-1]) / 20
        body_size = abs(close_prices[-1] - opens[-1])
        wick_size = (highs[-1] - lows[-1]) - body_size
        body_spike = body_size > ATR_BODY_MULTIPLIER * atr

        if rsi < RSI_OVERSOLD and vol_spike and body_spike:
            message = f"LONG SIGNAL:\nPair: {symbol}\nEntry Plan: After 10 sec\nExpected Move: +1.2%"
            send_alert(message)
        elif rsi > RSI_OVERBOUGHT and vol_spike and body_spike:
            message = f"SHORT SIGNAL:\nPair: {symbol}\nEntry Plan: After 10 sec\nExpected Move: -1.2%"
            send_alert(message)


if __name__ == '__main__':
    while True:
        print(f"Checking signals at {datetime.utcnow()}...")
        check_signals()
        time.sleep(180)  # Check every 3 minutes
