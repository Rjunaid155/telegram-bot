import requests
import json
import numpy as np
import pandas as pd
import os
import time
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from ta.momentum import RSIIndicator
from ta.trend import MACD
from textblob import TextBlob

# *🔹 Load API Credentials*
BITGET_API_URL = "https://api.bitget.com/api/v2/spot/market/orderbook?symbol=BTCUSDT"
MEMPOOL_URL = "https://mempool.space/api/mempool"
TELEGRAM_TOKEN = os.getenv("TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# *🔹 Fetch Order Book Data*
def get_order_book():
    try:
        response = requests.get(BITGET_API_URL)
        data = response.json()
        return data["data"]
    except Exception as e:
        print(f"Error fetching order book: {e}")
        return None

# *🔹 Fetch Mempool Data*
def get_mempool_data():
    try:
        response = requests.get(MEMPOOL_URL)
        return response.json()
    except Exception as e:
        print(f"Error fetching mempool data: {e}")
        return None

# *🔹 AI-Based Sentiment Analysis*
def analyze_sentiment(text):
    blob = TextBlob(text)
    return blob.sentiment.polarity

# *🔹 AI Model for Price Prediction (LSTM)*
def train_ai_model(price_data):
    X, Y = [], []
    for i in range(len(price_data) - 5):
        X.append(price_data[i:i+5])
        Y.append(price_data[i+5])
    X, Y = np.array(X), np.array(Y)

    model = Sequential([
        LSTM(50, activation='relu', input_shape=(5, 1)),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mse')
    model.fit(X, Y, epochs=10, batch_size=1, verbose=1)
    return model

# *🔹 Predict Next Price*
def predict_next_price(model, latest_prices):
    latest_prices = np.array(latest_prices).reshape(1, 5, 1)
    return model.predict(latest_prices)[0][0]

# *🔹 Technical Indicators Calculation*
def get_technical_indicators(price_data):
    df = pd.DataFrame({"close": price_data})
    df["rsi"] = RSIIndicator(df["close"]).rsi()
    df["macd"] = MACD(df["close"]).macd()
    return df.iloc[-1]["rsi"], df.iloc[-1]["macd"]

# *🔹 Send Trading Signal to Telegram*
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=data)

# *🔹 AI-Enhanced Trading Signal*
def trade_signal():
    order_book = get_order_book()
    if not order_book:
        return

    best_bid = float(order_book["bids"][0][0])
    best_ask = float(order_book["asks"][0][0])
    mempool_data = get_mempool_data()
    mempool_size = mempool_data.get("vsize", 0) if mempool_data else 0

    price_history = [30000, 30100, 30200, 30350, 30400]  # Replace with actual data
    rsi, macd = get_technical_indicators(price_history)
    ai_model = train_ai_model(price_history)
    predicted_price = predict_next_price(ai_model, price_history)

    if predicted_price > best_ask and rsi < 30 and macd > 0:
        message = f"🟢 Long Trade Alert 🟢\n💰 Best Ask: {best_ask}\n📊 RSI: {rsi}\n📈 MACD: {macd}\n🚀 Predicted Price: {predicted_price}"
        send_telegram_alert(message)
    elif predicted_price < best_bid and rsi > 70 and macd < 0:
        message = f"🔴 Short Trade Alert 🔴\n💰 Best Bid: {best_bid}\n📊 RSI: {rsi}\n📉 MACD: {macd}\n🔥 Predicted Price: {predicted_price}"
        send_telegram_alert(message)

# *🔹 Run the Trading Bot*
while True:
    trade_signal()
    time.sleep(60)  # Run every minute
