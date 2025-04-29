import requests
import pandas as pd
import time

# Telegram bot setup
TOKEN = 'TOKEN'
CHAT_ID = 'TELEGRAM_CHAT_ID'

def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    payload = {'chat_id': CHAT_ID, 'text': message}
    requests.post(url, data=payload)

def get_ohlcv(symbol, interval='15m', limit=100):
    url = f"https://api.mexc.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    data = response.json()

    # Adjusted column list for MEXC 8-element data
    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'turnover'
    ])
    df['close'] = df['close'].astype(float)
    return df

def calculate_rsi(data, period=14):
    delta = data['close'].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def trade(symbol, interval='15m', threshold_buy=30, threshold_sell=70):
    df = get_ohlcv(symbol, interval)
    df['RSI'] = calculate_rsi(df)

    current_rsi = df['RSI'].iloc[-1]
    price = df['close'].iloc[-1]

    if current_rsi <= threshold_buy:
        message = f"[LONG SIGNAL]\nSymbol: {symbol}\nRSI: {round(current_rsi,2)}\nPrice: {price}"
        send_telegram_message(message)

    elif current_rsi >= threshold_sell:
        message = f"[SHORT SIGNAL]\nSymbol: {symbol}\nRSI: {round(current_rsi,2)}\nPrice: {price}"
        send_telegram_message(message)
    else:
        print("No strong signal yet.")

def main():
    # Example symbol: BTCUSDT (MEXC format)
    trade('BTCUSDT', interval='15m', threshold_buy=30, threshold_sell=70)

if __name__ == '__main__':
    main()
