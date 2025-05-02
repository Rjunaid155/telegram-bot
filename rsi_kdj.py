import requests
import pandas as pd
import ta
from datetime import datetime

def fetch_symbols():
    return ['BTCUSDT', 'ETHUSDT', 'XRPUSDT']  # Apne hisab se coins daal le

def fetch_candles(symbol):
    url = f"https://api.mexc.com/api/v3/klines?symbol={symbol}&interval=5m&limit=100"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if not data:
            print(f"Skipping {symbol}: No candle data")
            return None
        df = pd.DataFrame(data, columns=['timestamp','open','high','low','close','volume',
                                         'close_time','quote_asset_volume','number_of_trades',
                                         'taker_buy_base_asset_volume','taker_buy_quote_asset_volume','ignore'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    else:
        print(f"Failed to fetch candles for {symbol}")
        return None
def calculate_rsi(series, period=14):
    return ta.momentum.RSIIndicator(close=series, window=period).rsi()

def calculate_kdj(df, period=14):
    low_min = df['low'].rolling(period).min()
    high_max = df['high'].rolling(period).max()
    rsv = (df['close'] - low_min) / (high_max - low_min) * 100
    k = rsv.ewm(com=2).mean()
    d = k.ewm(com=2).mean()
    j = 3 * k - 2 * d
    return j

def send_alert(message):
    print(message)  # Yahan apna Telegram ya webhook logic laga le

def check_signals():
    pairs = fetch_symbols()
    for symbol in pairs:
        df = fetch_candles(symbol)
        if df is None or len(df) < 20:
            continue

        df['rsi_5m'] = calculate_rsi(df['close'], 14)
        df['j'] = calculate_kdj(df, 14)
        avg_volume = df['volume'].iloc[:-1].mean()
        current_volume = df['volume'].iloc[-1]
        last_rsi = df['rsi_5m'].iloc[-1]
        last_j = df['j'].iloc[-1]
        price = df['close'].iloc[-1]

        # Yeh debug print:
        print(f"{symbol} | RSI: {last_rsi:.2f} | J: {last_j:.2f} | Vol: {current_volume:.2f} vs Avg: {avg_volume:.2f}")

        if last_rsi > 70 and last_j > 80 and current_volume > 1.5 * avg_volume:
            tp = round(price * 0.995, 4)
            sl = round(price * 1.005, 4)
            message = (
                f"⚠️ [SHORT SIGNAL] {symbol}\n"
                f"📊 Price: {price}\n"
                f"⛔ RSI 5m: {last_rsi:.2f}\n"
                f"⛔ J: {last_j:.2f}\n"
                f"🔥 Volume Spike: {current_volume:.2f} vs Avg {avg_volume:.2f}\n"
                f"✅ Entry: {price}\n"
                f"🎯 TP: {tp}\n"
                f"❌ SL: {sl}\n"
                f"🕒 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
            )
            send_alert(message)

check_signals()
