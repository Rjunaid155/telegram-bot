import requests
import time
import statistics
from datetime import datetime
import os
# === CONFIG ===
TELEGRAM_TOKEN = 'TOKEN'
CHAT_ID = 'TELEGRAM_CHAT_ID'
MEXC_BASE_URL = 'https://api.mexc.com'
ALERT_INTERVAL = 120  # seconds
RSI_THRESHOLD = 28  # Oversold threshold
MIN_STRENGTH = 80  # Minimum signal strength % to allow alert

# === TELEGRAM ALERT ===
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Telegram error: {e}")

# === FETCH SYMBOLS ===
def get_spot_symbols():
    try:
        res = requests.get(f"{MEXC_BASE_URL}/api/v3/ticker/24hr").json()
        filtered = [x for x in res if x['symbol'].endswith('USDT') and not x['symbol'].endswith('3SUSDT') and float(x['quoteVolume']) > 300000]
        sorted_coins = sorted(filtered, key=lambda x: float(x['quoteVolume']), reverse=True)
        return [x['symbol'] for x in sorted_coins]
    except Exception as e:
        print(f"Symbol fetch error: {e}")
        return []

# === FETCH KLINES ===
def get_klines(symbol, interval='15m', limit=100):
    try:
        url = f"{MEXC_BASE_URL}/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
        return requests.get(url).json()
    except Exception as e:
        print(f"Kline fetch error for {symbol}: {e}")
        return []

# === CALCULATE RSI ===
def calculate_rsi(closes, period=14):
    if len(closes) < period:
        return 50
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [d for d in deltas if d > 0]
    losses = [-d for d in deltas if d < 0]
    avg_gain = sum(gains) / period if gains else 0
    avg_loss = sum(losses) / period if losses else 1
    rs = avg_gain / avg_loss if avg_loss != 0 else 0
    rsi = 100 - (100 / (1 + rs))
    return rsi

# === FETCH ORDERBOOK ===
def get_orderbook(symbol):
    try:
        url = f"{MEXC_BASE_URL}/api/v3/depth?symbol={symbol}&limit=50"
        orderbook = requests.get(url).json()
        bids = orderbook['bids']
        asks = orderbook['asks']
        total_bids = sum(float(b[1]) for b in bids)
        total_asks = sum(float(a[1]) for a in asks)
        top_bid = float(bids[0][0]) if bids else 0
        top_ask = float(asks[0][0]) if asks else 0
        pressure = 'UP' if total_bids > total_asks else 'DOWN'
        suggested_price = (top_bid + top_ask) / 2
        return pressure, suggested_price
    except Exception as e:
        print(f"Orderbook fetch error for {symbol}: {e}")
        return 'UNKNOWN', 0

# === ANALYZE COIN ===
def analyze_coin(symbol):
    klines_15m = get_klines(symbol, '15m')
    klines_1h = get_klines(symbol, '1h')

    if not klines_15m or not klines_1h:
        return None

    closes_15m = [float(k[4]) for k in klines_15m]
    volumes_15m = [float(k[5]) for k in klines_15m]
    closes_1h = [float(k[4]) for k in klines_1h]

    # Calculate RSIs
    rsi_15m = calculate_rsi(closes_15m)
    rsi_1h = calculate_rsi(closes_1h)

    # ATR spike detection
    price_moves = [abs(closes_15m[i] - closes_15m[i-1]) for i in range(1, len(closes_15m))]
    atr = statistics.mean(price_moves[-14:]) if len(price_moves) >= 14 else 0
    last_move = price_moves[-1] if price_moves else 0
    atr_spike = last_move > atr * 1.5

    # Volume Spike Detection
    avg_volume = statistics.mean(volumes_15m[:-2]) if len(volumes_15m) > 2 else 0
    last_volume = volumes_15m[-1]
    volume_spike = last_volume > avg_volume * 2

    # Orderbook
    pressure, suggested_price = get_orderbook(symbol)

    # Final Decision
    strength = 0
    if rsi_15m < RSI_THRESHOLD and rsi_1h < RSI_THRESHOLD:
        strength += 40
    if atr_spike:
        strength += 30
    if volume_spike:
        strength += 20
    if pressure == 'UP':
        strength += 10

    print(f"[DEBUG] {symbol}: RSI15m={rsi_15m:.2f}, RSI1h={rsi_1h:.2f}, ATRSpike={atr_spike}, VolumeSpike={volume_spike}, Strength={strength}%")

    if strength >= MIN_STRENGTH:
        return {
            'symbol': symbol,
            'price': round(suggested_price, 5),
            'tp': round(suggested_price * 1.02, 5),  # Suggest 2% Target
            'strength': strength
        }
    else:
        return None

# === MAIN LOOP ===
def main():
    print("Starting Strong Spot Signal Scanner (MEXC)...")
    while True:
        try:
            coins = get_spot_symbols()
            print(f"[INFO] Scanning {len(coins)} coins...")
            for coin in coins:
                signal = analyze_coin(coin)
                if signal:
                    msg = f"<b>[SPOT BUY ALERT]</b>\n" \
                          f"Coin: <code>{signal['symbol']}</code>\n" \
                          f"Suggested Buy Price: <b>${signal['price']}</b>\n" \
                          f"Suggested Target: <b>${signal['tp']}</b>\n" \
                          f"Signal Strength: <b>{signal['strength']}%</b>\n" \
                          f"Time: {datetime.now().strftime('%H:%M:%S')}\n\n" \
                          f"Reason: Strong Oversold Zone + Volume Spike + ATR Spike + Orderbook Pressure"
                    send_telegram_alert(msg)
        except Exception as e:
            print(f"Main loop error: {e}")

        time.sleep(ALERT_INTERVAL)

if __name__ == '__main__':
    main()
