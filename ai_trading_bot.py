import os
import time
import requests
import numpy as np
import pandas as pd
import telebot
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from datetime import datetime

# 🔑 Bitget API Keys
API_KEY = os.getenv("BITGET_API_KEY")
SECRET_KEY = os.getenv("BITGET_SECRET_KEY")
PASSPHRASE = os.getenv("BITGET_PASSPHRASE")
TELEGRAM_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# 📊 Fetch historical data from Bitget
def fetch_klines(symbol, limit=100):
    url = f"https://api.bitget.com/api/mix/v1/market/candles?symbol={symbol}_UMCBL&granularity=900"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()["data"]
        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df = df.iloc[::-1].astype(float)
        return df
    else:
        print("Error fetching market data:", response.text)
        return None

# 📈 Technical Indicators
def calculate_indicators(df):
    df["EMA_50"] = EMAIndicator(df["close"], window=50).ema_indicator()
    df["EMA_200"] = EMAIndicator(df["close"], window=200).ema_indicator()
    df["MACD"] = MACD(df["close"]).macd()
    df["RSI"] = RSIIndicator(df["close"]).rsi()
    return df.dropna()

# 🚀 AI Model (SVM)
def train_ai_model(df):
    X = df[["EMA_50", "EMA_200", "MACD", "RSI"]]
    y = np.where(df["close"].shift(-1) > df["close"], 1, 0)  # 1 = LONG, 0 = SHORT

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = SVC(kernel="rbf", probability=True)
    model.fit(X_scaled, y)

    return model, scaler

# 📊 Generate AI-based signals
def generate_ai_signal(symbol):
    df = fetch_klines(symbol)
    if df is not None:
        df = calculate_indicators(df)
        model, scaler = train_ai_model(df)

        latest_data = df.iloc[-1][["EMA_50", "EMA_200", "MACD", "RSI"]].values.reshape(1, -1)
        latest_data_scaled = scaler.transform(latest_data)
        prediction = model.predict(latest_data_scaled)
        confidence = model.predict_proba(latest_data_scaled)[0][prediction[0]] * 100

        signal_type = "LONG" if prediction[0] == 1 else "SHORT"
        entry_price = round(df["close"].iloc[-1], 2)
        stop_loss = round(entry_price * (0.99 if signal_type == "LONG" else 1.01), 2)
        target = round(entry_price * (1.02 if signal_type == "LONG" else 0.98), 2)

        message = (
            f"🚀 AI-Based Trading Signal 🚀\n"
            f"✅ {symbol}/USDT (Futures) - {signal_type}\n"
            f"📉 Entry Price: ${entry_price}\n"
            f"📈 Target: ${target}\n"
            f"🛑 Stop Loss: ${stop_loss}\n"
            f"🔥 Confidence: {confidence:.2f}%"
        )
        bot.send_message(CHAT_ID, message)

# ✅ Run the bot
if __name__ == "__main__":
    trading_pairs = ["BTCUSDT", "ETHUSDT"]  # Add more pairs if needed
    for pair in trading_pairs:
        generate_ai_signal(pair)
