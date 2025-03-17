import requests
import pandas as pd
import pandas_ta as ta

def get_bitget_data(symbol, interval="5m", limit=100):
    url = f"https://api.bitget.com/api/spot/v1/market/candles?symbol={symbol}&period={interval}&limit={limit}"
    response = requests.get(url)
    data = response.json()
    
    # Creating a DataFrame with time and close prices
    df = pd.DataFrame(data['data'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['close'] = df['close'].astype(float)
    
    return df

def calculate_indicators(df):
    # Calculate MACD
    macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
    df['MACD'], df['MACD_signal'], df['MACD_diff'] = macd.iloc[:, 0], macd.iloc[:, 1], macd.iloc[:, 2]

    # Calculate RSI
    df['RSI'] = ta.rsi(df['close'], length=14)

    # Calculate EMA
    df['EMA'] = ta.ema(df['close'], length=9)

    # Calculate Bollinger Bands
    bb = ta.bbands(df['close'], length=20, std=2)
    df['BB_upper'], df['BB_middle'], df['BB_lower'] = bb.iloc[:, 0], bb.iloc[:, 1], bb.iloc[:, 2]

    return df

def check_and_alert_short(symbol):
    df = get_bitget_data(symbol)
    if df is not None:
        indicators = calculate_indicators(df)

        # Check Bollinger Band and generate alert for short signals
        if indicators['close'].iloc[-1] < indicators['BB_lower'].iloc[-1]:
            print(f"Short signal for {symbol}: Price below Bollinger Band lower bound")
        
        # Print other indicators for confirmation
        print(f"MACD: {indicators['MACD'].iloc[-1]}, RSI: {indicators['RSI'].iloc[-1]}")
        print(f"Bollinger Bands: Upper={indicators['BB_upper'].iloc[-1]}, Lower={indicators['BB_lower'].iloc[-1]}")

        # Send alert via Telegram
        message = f"Short signal for {symbol}: MACD={indicators['MACD'].iloc[-1]}, RSI={indicators['RSI'].iloc[-1]}"
        send_telegram_alert(message)

def send_telegram_alert(message):
    # Replace with your actual Telegram bot token and chat ID
    bot_token = 'your_bot_token'
    chat_id = 'your_chat_id'
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {'chat_id': chat_id, 'text': message}
    response = requests.get(url, params=params)
    return response.json()

if __name__ == "__main__":
    symbol = "BTCUSDT"
    check_and_alert_short(symbol)
