import numpy as np
import requests
import json
import time
import os
from textblob import TextBlob
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense

# ✅ Load API Credentials from Environment Variables
TELEGRAM_TOKEN = os.getenv("TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BITGET_ORDER_BOOK_URL = "https://api.bitget.com/api/v2/spot/market/orderbook?symbol=BTCUSDT"
MEMPOOL_URL = "https://mempool.space/api/mempool"

# ✅ Function to fetch Bitget order book data
def get_bitget_order_book():
    try:
        response = requests.get(BITGET_ORDER_BOOK_URL)
        data = response.json()
        return data
    except Exception as e:
        print(f"Error fetching Bitget Order Book: {e}")
        return None

# ✅ Function to fetch Mempool.space data
def get_mempool_data():
    try:
        response = requests.get(MEMPOOL_URL)
        data = response.json()
        return data
    except Exception as e:
        print(f"Error fetching Mempool Data: {e}")
        return None

# ✅ Function to analyze sentiment using TextBlob
def analyze_sentiment(text):
    blob = TextBlob(text)
    return blob.sentiment.polarity

# ✅ Function to send Telegram alerts
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    response = requests.post(url, data=data)
    return response.json()

# ✅ AI Model for Predicting Market Trends (LSTM)
def train_ai_model(price_history):
    price_history = np.array(price_history)

    # 🔹 Ensure 3D Shape for LSTM (samples, timesteps, features)
    price_history = price_history.reshape((1, price_history.shape[0], 1))

    # 🔹 Define LSTM Model
    model = Sequential([
        LSTM(50, return_sequences=True, input_shape=(price_history.shape[1], 1)),
        LSTM(50, return_sequences=False),
        Dense(1)  # Output Layer
    ])

    model.compile(optimizer='adam', loss='mse')

    # 🔹 Train Model (Fake y_train for now)
    y_train = np.zeros((1, 1))  # Placeholder
    model.fit(price_history, y_train, epochs=10, batch_size=8, verbose=1)

    return model

# ✅ Main function to fetch data and analyze signals
def main():
    print("Fetching data...")

    # 🔹 Get Bitget Order Book Data
    order_book = get_bitget_order_book()
    if order_book and "data" in order_book:
        best_bid = float(order_book["data"]["bids"][0][0])
        best_ask = float(order_book["data"]["asks"][0][0])
    else:
        best_bid, best_ask = None, None

    # 🔹 Get Mempool Data
    mempool_data = get_mempool_data()
    mempool_size = mempool_data.get("vsize", None)

    # 🔹 Sample text for sentiment analysis
    sample_text = "Bitcoin is going to the moon!"
    sentiment_score = analyze_sentiment(sample_text)

    # 🔹 Fake Price Data for AI Model Training (Replace with Real Data)
    price_history = [best_bid, best_ask, best_bid - best_ask, mempool_size, sentiment_score]
    model = train_ai_model(price_history)

    # 🔹 AI Prediction (Just a Dummy Example)
    prediction = model.predict(np.array(price_history).reshape((1, len(price_history), 1)))[0][0]

    # ✅ Decision Making
    if best_bid and best_ask and mempool_size:
        if sentiment_score < -0.3 and mempool_size > 100000:
            message = f"🔴 Short Trade Alert 🔴\n\n📉 Bitcoin Short Signal Detected!\n\n💰 Best Bid: {best_bid}\n💰 Best Ask: {best_ask}\n🚀 Mempool Size: {mempool_size}\n📊 Sentiment Score: {sentiment_score}\n🔮 AI Prediction: {prediction}\n\n📢 Action: Strong Short Signal!"
            send_telegram_alert(message)
        else:
            print("No strong short signal detected.")

if __name__ == "__main__":
    main()
