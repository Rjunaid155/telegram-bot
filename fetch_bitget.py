import pandas as pd
import pandas_ta as ta  # Pandas-ta for technical indicators
import ccxt
import time

# Initialize the Bitget exchange using ccxt
bitget = ccxt.bitget({
    'apiKey': 'YOUR_API_KEY',
    'secret': 'YOUR_SECRET_KEY',
    'enableRateLimit': True,
})

# Function to fetch OHLCV data (Open, High, Low, Close, Volume)
def fetch_ohlcv(symbol, timeframe='5m', limit=100):
    return bitget.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

# Function to apply indicators and generate signals
def apply_indicators(df):
    # Add indicators
    df['EMA_9'] = ta.ema(df['close'], length=9)
    df['RSI'] = ta.rsi(df['close'], length=14)
    df['MACD'], df['MACD_signal'], df['MACD_hist'] = ta.macd(df['close'], fast=12, slow=26, signal=9)
    df['Bollinger_upper'], df['Bollinger_middle'], df['Bollinger_lower'] = ta.bbands(df['close'], length=20)
    
    # Generate signals (example logic for long/short)
    df['long_signal'] = (df['close'] > df['EMA_9']) & (df['RSI'] < 70)
    df['short_signal'] = (df['close'] < df['EMA_9']) & (df['RSI'] > 30)

    return df

# Fetch data and apply indicators
def main():
    symbol = 'BTC/USDT'  # Change this to your desired altcoin
    timeframe = '5m'  # 5-minute timeframe
    limit = 100  # Limit of 100 candles
    
    while True:
        try:
            ohlcv = fetch_ohlcv(symbol, timeframe, limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Apply indicators
            df = apply_indicators(df)

            # Check for signals
            if df['long_signal'].iloc[-1]:
                print(f"Long signal for {symbol}")
            elif df['short_signal'].iloc[-1]:
                print(f"Short signal for {symbol}")

        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(300)  # Run every 5 minutes

if __name__ == "__main__":
    main()
