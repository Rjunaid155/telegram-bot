import requests
import pandas as pd
import pandas_ta as ta

def get_bitget_data(symbol):
    url = f"https://api.bitget.com/api/spot/v1/market/tickers?symbol={symbol}"
    response = requests.get(url)
    data = response.json()

    # Extract price data
    df = pd.DataFrame(data['data'])
    df['close'] = df['close'].astype(float)
    
    return df

def calculate_indicators(df):
    # Calculate MACD
    df['MACD'], df['MACD_signal'], df['MACD_diff'] = ta.macd(df['close'], fast=12, slow=26, signal=9)

    # Calculate RSI
    df['RSI'] = ta.rsi(df['close'], length=14)

    # Calculate EMA
    df['EMA'] = ta.ema(df['close'], length=9)

    # Calculate Bollinger Bands
    bb = ta.bbands(df['close'], length=20, std=2)
    df['BB_upper'], df['BB_middle'], df['BB_lower'] = bb['BBU_20_2.0'], bb['BBM_20_2.0'], bb['BBL_20_2.0']

    return df

def check_and_alert_short(symbol):
    df = get_bitget_data(symbol)
    if df is not None:
        indicators = calculate_indicators(df)

        # Bollinger Band conditions
        if indicators['close'].iloc[-1] < indicators['BB_lower'].iloc[-1]:
            print(f"Short signal for {symbol}: Price below Bollinger Band lower bound")

        # Other indicators
        print(f"MACD: {indicators['MACD'].iloc[-1]}, RSI: {indicators['RSI'].iloc[-1]}")

if __name__ == "__main__":
    symbol = "BTCUSDT"
    check_and_alert_short(symbol)
