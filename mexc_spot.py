import requests
import time
import os
import statistics
from datetime import datetime

# === CONFIG ===
TELEGRAM_TOKEN = 'TOKEN'
CHAT_ID = 'TELEGRAM_CHAT_ID'
MEXC_BASE_URL = 'https://api.mexc.com'
ALERT_INTERVAL = 120  # seconds

# === TELEGRAM ALERT ===
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Telegram error: {e}")

# === FETCH COINS ===
def get_spot_symbols():
    url = f"{MEXC_BASE_URL}/api/v3/ticker/24hr"
    try:
        res = requests.get(url).json()
        filtered = [x for x in res if x['symbol'].endswith('USDT') and not x['symbol'].endswith('3SUSDT') and float(x['quoteVolume']) > 500000]
        sorted_coins = sorted(filtered, key=lambda x: float(x['quoteVolume']), reverse=True)[:50]
        return [x['symbol'] for x in sorted_coins]
    except Exception as e:
        print(f"Symbol fetch error: {e}")
        return []

# === FETCH KLINES ===
def get_klines(symbol, interval='15m', limit=20):
    url = f"{MEXC_BASE_URL}/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        return requests.get(url).json()
    except Exception as e:
        print(f"Kline fetch error for {symbol}: {e}")
        return []

# === ANALYZE COIN ===
def analyze_coin(symbol):
    klines = get_klines(symbol)
    if not klines or len(klines) < 5:
        print(f"[SKIP] Not enough klines for {symbol}")
        return None

    closes = [float(k[4]) for k in klines]
    volumes = [float(k[5]) for k in klines]

    current_price = closes[-1]
    previous_close = closes[-2]
    avg_volume = statistics.mean(volumes[:-2])
    volume_spike = volumes[-1] > avg_volume * 2
    price_change = ((current_price - previous_close) / previous_close) * 100

    print(f"[DEBUG] {symbol}: PriceChange={price_change:.2f}%, VolumeSpike={volume_spike}")

    if volume_spike and price_change > 0.2:
        print(f"[ALERT] Strong signal found for {symbol}")
        return {
            'symbol': symbol,
            'price': round(current_price, 5),
            'tp': round(current_price * 1.05, 5),
            'sl': round(current_price * 0.98, 5),
            'change': round(price_change, 2),
            'strength': round((price_change + (volumes[-1]/avg_volume)) * 4, 1)
        }
    return None

# === MAIN LOOP ===
def main():
    print("Starting Spot Signal Scanner (MEXC)...")
    while True:
        try:
            coins = get_spot_symbols()
            print(f"[INFO] Scanning {len(coins)} coins...")
            for coin in coins:
                print(f"[SCAN] {coin}")
                signal = analyze_coin(coin)
                if signal:
                    msg = f"<b>[SPOT BUY ALERT]</b>\n" \
                          f"Coin: <code>{signal['symbol']}</code>\n" \
                          f"Buy Price: <b>${signal['price']}</b>\n" \
                          f"Target: ${signal['tp']}\n" \
                          f"Stoploss: ${signal['sl']}\n" \
                          f"Strength: {signal['strength']}%\n" \
                          f"Time: {datetime.now().strftime('%H:%M:%S')}\n\n" \
                          f"Reason: Volume Spike"
                    send_telegram_alert(msg)
        except Exception as e:
            print(f"Main loop error: {e}")

        time.sleep(ALERT_INTERVAL)

if __name__ == '__main__':
    main()
