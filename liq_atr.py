import requests
import time
import datetime
import os
from statistics import mean

# Telegram config
BOT_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Signal settings
LEVERAGE = 50
RSI_OVERBOUGHT = 85
RSI_OVERSOLD = 15
ATR_MULTIPLIER = 1.5
VOLUME_SPIKE_MULTIPLIER = 2

def send_telegram_alert(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram error:", e)

def get_usdt_pairs():
    url = "https://api.bitget.com/api/mix/v1/market/contracts?productType=umcbl"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        return [x['symbol'] for x in data.get('data', [])]
    except Exception as e:
        print("Error fetching pairs:", e)
        return []

def get_kline(symbol, interval, limit=100):
    url = "https://api.bitget.com/api/mix/v1/market/depth"
    params = {
        "symbol": symbol,
        "productType": "USDT-FUTURES",
        "granularity": interval,
        "limit": limit
    }
    try:
        res = requests.get(url, params=params, timeout=10).json()
        return [[float(x[1]), float(x[2]), float(x[3]), float(x[4]), float(x[5]), int(x[0])] for x in res['data']]
    except Exception as e:
        print(f"Kline error for {symbol}:", e)
        return []

def calculate_rsi(closes, period=14):
    gains, losses = [], []
    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]
        gains.append(max(0, change))
        losses.append(max(0, -change))
    avg_gain = mean(gains[-period:])
    avg_loss = mean(losses[-period:])
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

def calculate_atr(candles, period=14):
    trs = []
    for i in range(1, len(candles)):
        high, low, prev_close = candles[i][1], candles[i][2], candles[i - 1][4]
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)
    return round(mean(trs[-period:]), 6)

def calculate_liquidation(entry, side):
    if side == "LONG":
        return round(entry - ((entry / LEVERAGE) * 0.98), 6)
    else:
        return round(entry + ((entry / LEVERAGE) * 0.98), 6)

def analyze(symbol):
    tf_map = {'1m': 60, '3m': 180, '5m': 300}
    for tf, sec in tf_map.items():
        candles = get_kline(symbol, sec, 100)
        if not candles:
            continue

        closes = [x[4] for x in candles]
        volumes = [x[5] for x in candles]
        atr = calculate_atr(candles)
        rsi = calculate_rsi(closes)
        last_volume = volumes[-1]
        avg_volume = mean(volumes[-10:-1])
        body_size = abs(candles[-1][1] - candles[-1][2])
        entry = closes[-1]
        alert_time = datetime.datetime.utcfromtimestamp(candles[-1][5]/1000 + sec).strftime("%H:%M:%S")

        if rsi >= RSI_OVERBOUGHT and last_volume > avg_volume * VOLUME_SPIKE_MULTIPLIER and body_size > atr * ATR_MULTIPLIER:
            liq = calculate_liquidation(entry, "SHORT")
            msg = (
                f"⚠️ {symbol} SHORT Signal ({tf}):\n"
                f"Entry: {entry}\n"
                f"RSI: {rsi}\n"
                f"Liquidation (50x): {liq}\n"
                f"Time: {alert_time}\n"
                f"Reason: RSI>{RSI_OVERBOUGHT}, Volume Spike, Big Candle"
            )
            send_telegram_alert(msg)
            return

        if rsi <= RSI_OVERSOLD and last_volume > avg_volume * VOLUME_SPIKE_MULTIPLIER and body_size > atr * ATR_MULTIPLIER:
            liq = calculate_liquidation(entry, "LONG")
            msg = (
                f"⚡ {symbol} LONG Signal ({tf}):\n"
                f"Entry: {entry}\n"
                f"RSI: {rsi}\n"
                f"Liquidation (50x): {liq}\n"
                f"Time: {alert_time}\n"
                f"Reason: RSI<{RSI_OVERSOLD}, Volume Spike, Big Candle"
            )
            send_telegram_alert(msg)
            return

def main():
    while True:
        try:
            print("⏳ Scanning Bitget Futures...")
            coins = get_usdt_pairs()
            for coin in coins:
                analyze(coin)
            time.sleep(60)
        except Exception as e:
            print("Main error:", e)
            time.sleep(10)

if __name__ == "__main__":
    main()
