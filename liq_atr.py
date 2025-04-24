# Merged Spike + Order Book Alert Bot for Telegram (Bitget API)

import requests
import time
import os
import hmac
import hashlib
import base64
import telebot
from datetime import datetime, timedelta
from statistics import mean

# --- Config ---
API_KEY = os.getenv("BITGET_API_KEY")
SECRET_KEY = os.getenv("BITGET_SECRET_KEY")
PASSPHRASE = os.getenv("BITGET_PASSPHRASE")
TELEGRAM_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

WALLET_USD = 100
LEVERAGE = 50
RSI_OVERBOUGHT = 85
RSI_OVERSOLD = 15
ATR_MULTIPLIER = 1.5
VOLUME_SPIKE_MULTIPLIER = 2

def send_telegram_alert(message):
    bot.send_message(CHAT_ID, message)

def generate_signature(timestamp, method, request_path, body=""):
    message = f"{timestamp}{method}{request_path}{body}"
    signature = hmac.new(SECRET_KEY.encode(), message.encode(), hashlib.sha256).digest()
    return base64.b64encode(signature).decode()

def fetch_order_book(market_type, symbol, limit=5):
    if market_type == "spot":
        base_url = "https://api.bitget.com/api/spot/v1/market/depth"
        symbol = f"{symbol}_SPBL"
    elif market_type == "futures":
        base_url = "https://api.bitget.com/api/mix/v1/market/depth"
        symbol = f"{symbol}_UMCBL"
    else:
        return None
    params = {"symbol": symbol, "limit": limit}
    response = requests.get(base_url, params=params)
    return response.json() if response.status_code == 200 else None

def get_usdt_pairs():
    url = "https://api.bitget.com/api/v2/mix/market/tickers?productType=USDT-FUTURES"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        return [x['symbol'] for x in data.get('data', []) if isinstance(data['data'], list)]
    except Exception as e:
        print("Error in get_usdt_pairs:", e)
        return []

def get_kline(symbol, interval, limit=100):
    url = f"https://api.bitget.com/api/v2/mix/market/candles"
    params = {
        "symbol": symbol,
        "productType": "USDT-FUTURES",
        "granularity": interval,
        "limit": limit
    }
    res = requests.get(url, params=params).json()
    return [[float(x[1]), float(x[2]), float(x[3]), float(x[4]), float(x[5]), int(x[0])] for x in res.get('data', [])]

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
        high = candles[i][1]
        low = candles[i][2]
        prev_close = candles[i - 1][4]
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
        alert_time = datetime.utcfromtimestamp(candles[-1][5]/1000 + sec).strftime("%H:%M:%S")

        if rsi >= RSI_OVERBOUGHT and last_volume > avg_volume * VOLUME_SPIKE_MULTIPLIER and body_size > atr * ATR_MULTIPLIER:
            liq = calculate_liquidation(entry, "SHORT")
            msg = (
                f"Coin: {symbol}\nSignal: SHORT\nTimeframe: {tf}\nEntry: {entry}\n"
                f"Liq: {liq}\nTime: {alert_time}\nReason: RSI>{RSI_OVERBOUGHT}, Volume Spike, ATR Surge"
            )
            send_telegram_alert(msg)
            return

        if rsi <= RSI_OVERSOLD and last_volume > avg_volume * VOLUME_SPIKE_MULTIPLIER and body_size > atr * ATR_MULTIPLIER:
            liq = calculate_liquidation(entry, "LONG")
            msg = (
                f"Coin: {symbol}\nSignal: LONG\nTimeframe: {tf}\nEntry: {entry}\n"
                f"Liq: {liq}\nTime: {alert_time}\nReason: RSI<{RSI_OVERSOLD}, Volume Spike, ATR Surge"
            )
            send_telegram_alert(msg)
            return

def order_book_signal(symbol):
    data = fetch_order_book("futures", symbol)
    if not data or "data" not in data:
        return None
    try:
        best_bid = float(data["data"]["bids"][0][0])
        stop_loss = round(best_bid * 1.005, 4)
        take_profit = round(best_bid * 0.995, 4)
        msg = (
            f"\n\u26a1 {symbol} SHORT Order Book Signal:\n"
            f"Entry: {best_bid}\nStop Loss: {stop_loss}\nTake Profit: {take_profit}"
        )
        return msg
    except:
        return None

def main():
    while True:
        try:
            print("\nScanning...")
            coins = get_usdt_pairs()
            for symbol in coins:
                analyze(symbol)
                ob_msg = order_book_signal(symbol)
                if ob_msg:
                    send_telegram_alert(ob_msg)
            time.sleep(60)
        except Exception as e:
            print("Error:", e)
            time.sleep(10)

if __name__ == "__main__":
    main()
