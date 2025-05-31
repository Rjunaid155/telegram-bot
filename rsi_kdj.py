import requests
import pandas as pd
import ta
import time
import telegram

# Telegram config
bot_token = 'YOUR_TELEGRAM_BOT_TOKEN'
chat_id = 'YOUR_CHAT_ID'
bot = telegram.Bot(token=bot_token)

# Fetch all symbols
def get_symbols():
    url = "https://contract.mexc.com/api/v1/contract/detail"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            symbols = [item['symbol'] for item in data['data']]
            return symbols
    except:
        return []
    return []

# Fetch candles
def fetch_candles(symbol):
    url = f"https://contract.mexc.com/api/v1/klines?symbol={symbol}&interval=5m&limit=100"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json().get('data')
            if not data:
                return None
            df = pd.DataFrame(data, columns=['open_time', 'open', 'high', 'low', 'close', 'volume'])
            df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
            df.set_index('open_time', inplace=True)
            df = df.astype(float, errors='ignore')
            return df
    except:
        return None
    return None

# RSI & KDJ calculation
def analyze_symbol(symbol):
    df = fetch_candles(symbol)
    if df is None or df.empty:
        return

    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    df['k'] = ta.momentum.stoch(df['high'], df['low'], df['close'], window=14, smooth_window=3)
    df['d'] = df['k'].rolling(3).mean()

    last_rsi = df['rsi'].iloc[-1]
    last_k = df['k'].iloc[-1]
    last_d = df['d'].iloc[-1]

    # Signal condition (example)
    if last_rsi < 30 and last_k < 20 and last_d < 20:
        message = f"🔔 {symbol} Oversold Alert!\nRSI: {last_rsi:.2f}, K: {last_k:.2f}, D: {last_d:.2f}"
        bot.send_message(chat_id=chat_id, text=message, parse_mode=telegram.ParseMode.MARKDOWN)

# Main loop
def run_scanner():
    symbols = get_symbols()
    print(f"Fetched {len(symbols)} symbols")
    for symbol in symbols:
        analyze_symbol(symbol)
        time.sleep(0.5)  # 0.5 sec delay to avoid rate limit

if __name__ == "__main__":
    run_scanner()
