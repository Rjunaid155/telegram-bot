import os
import requests
import numpy as np
import time
from ta.momentum import RSIIndicator

TELEGRAM_BOT_TOKEN = os.getenv('TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
MEXC_API_URL = 'https://api.mexc.com'

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Failed to send alert: {e}")

def fetch_all_symbols():
    try:
        response = requests.get(f"{MEXC_API_URL}/api/v3/exchangeInfo", timeout=10)
        data = response.json()
        return [s['symbol'] for s in data['symbols'] if s['quoteAsset'] == 'USDT']
    except Exception as e:
        print(f"Symbol fetch error: {e}")
        return []

def fetch_kline(symbol, interval='15m', limit=50):
    try:
        url = f"{MEXC_API_URL}/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
        response = requests.get(url, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Kline fetch error for {symbol}: {e}")
        return None

def fetch_orderbook(symbol):
    try:
        url = f"{MEXC_API_URL}/api/v3/depth?symbol={symbol}&limit=5"
        response = requests.get(url, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Orderbook fetch error for {symbol}: {e}")
        return None

def calculate_rsi(closes, window=14):
    if len(closes) < window:
        return np.array([])
    indicator = RSIIndicator(close=pd.Series(closes), window=window)
    return indicator.rsi().values

def detect_spike(candles):
    if not candles or len(candles) < 2:
        return False
    last_close = float(candles[-1][4])
    prev_close = float(candles[-2][4])
    change = ((last_close - prev_close) / prev_close) * 100
    return abs(change) > 1

def analyze_symbol(symbol):
    candles_15m = fetch_kline(symbol, '15m', 50)
    candles_1h = fetch_kline(symbol, '1h', 50)
    if not candles_15m or not candles_1h:
        return None

    closes_15m = np.array([float(c[4]) for c in candles_15m if len(c) > 4])
    closes_1h = np.array([float(c[4]) for c in candles_1h if len(c) > 4])
    if len(closes_1h) < 20:
        return None

    rsi_15m = calculate_rsi(closes_15m)
    rsi_1h = calculate_rsi(closes_1h)

    if len(rsi_15m) == 0 or len(rsi_1h) == 0:
        return None

    last_rsi_15m = rsi_15m[-1]
    last_rsi_1h = rsi_1h[-1]

    if last_rsi_15m > 30 or last_rsi_1h > 35:
        return None

    if not detect_spike(candles_15m):
        return None

    orderbook = fetch_orderbook(symbol)
    if not orderbook or 'bids' not in orderbook or 'asks' not in orderbook:
        return None

    bid_volume = sum(float(b[1]) for b in orderbook['bids'])
    ask_volume = sum(float(a[1]) for a in orderbook['asks'])

    if bid_volume <= ask_volume:
        return None

    # Target price suggestion
    best_bid_price = float(orderbook['bids'][0][0])
    tp_price = best_bid_price * 1.005  # Example: 0.5% Target

    return {
        'symbol': symbol,
        'entry_price': best_bid_price,
        'target_price': tp_price
    }

def main():
    print("Starting Strong Spot Signal Scanner (MEXC)...")
    all_symbols = fetch_all_symbols()
    print(f"[INFO] {len(all_symbols)} coins loaded.")

    while True:
        try:
            for symbol in all_symbols:
                signal = analyze_symbol(symbol)
                if signal:
                    message = (
                        f"Strong Spot Signal Detected!\n\n"
                        f"Coin: {signal['symbol']}\n"
                        f"Entry Price: {signal['entry_price']:.4f}\n"
                        f"Target Price: {signal['target_price']:.4f}\n"
                        f"Exchange: MEXC Spot\n"
                        f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    print(f"[ALERT] {symbol}")
                    send_telegram_alert(message)

            print("[INFO] Scan complete. Sleeping 60 seconds...")
            time.sleep(60)

        except Exception as e:
            print(f"Main loop error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
