import sys
import requests
import numpy as np
import tensorflow as tf
from telegram import Bot
from bitget_api import fetch_order_book, fetch_mempool_data, fetch_sentiment_score  # Custom functions
from indicators import calculate_atr  # ATR calculation function

# ✅ Ensure Correct Import Path
sys.path.append("/opt/render/project/src")  # Apne project ka exact path yahan likho

# ✅ Telegram Bot Setup
TELEGRAM_BOT_TOKEN = "TOKEN"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# ✅ AI Model Load
try:
    model = tf.keras.models.load_model("ai_price_prediction_model.h5")
except Exception as e:
    print(f"⚠️ AI Model Loading Error: {e}")
    model = None  # Model ko optional banaya, taake script crash na ho

# ✅ Fetch Data Function
def fetch_data():
    try:
        order_book = fetch_order_book("BTCUSDT")
        mempool_data = fetch_mempool_data()
        sentiment_score = fetch_sentiment_score()

        best_bid = order_book['best_bid']
        best_ask = order_book['best_ask']
        volume = order_book['volume']
        mempool_size = mempool_data['size']

        # AI Price Prediction (Agar Model Available hai)
        if model:
            price_history = np.array([best_bid, best_ask, volume, mempool_size, sentiment_score]).reshape(1, 5, 1)
            predicted_price = model.predict(price_history)[0][0]
        else:
            predicted_price = None  # Agar model load nahi hua, to default None

        return best_bid, best_ask, volume, mempool_size, sentiment_score, predicted_price

    except Exception as e:
        print(f"⚠️ Data Fetching Error: {e}")
        return None, None, None, None, None, None

# ✅ Generate Signal
def generate_signal():
    best_bid, best_ask, volume, mempool_size, sentiment_score, predicted_price = fetch_data()

    if None in [best_bid, best_ask, volume, mempool_size, sentiment_score]:  
        print("⚠️ Data fetch failed, skipping signal generation.")
        return  

    atr = calculate_atr("BTCUSDT", period=14)  # ATR for Stop Loss/Take Profit
    stop_loss = round(best_bid - (atr * 1.5), 2)
    take_profit = round(best_bid + (atr * 2.5), 2)

    # 🔴 Short Signal Logic
    if predicted_price and predicted_price < best_bid * 0.99 and sentiment_score < -0.1 and mempool_size > 50000:
        message = f"🔴 Short Trade Alert 🔴\n\n📉 AI Predicts Drop!\n💰 Best Bid: {best_bid}\n💰 Best Ask: {best_ask}\n🚀 Mempool Size: {mempool_size}\n📊 Sentiment Score: {sentiment_score}\n🔮 AI Prediction: {predicted_price}\n🎯 SL: {stop_loss} | TP: {take_profit}\n\n📢 Action: Enter Short Position!"
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="Markdown")

    # 🟢 Long Signal Logic
    elif predicted_price and predicted_price > best_bid * 1.01 and sentiment_score > 0.1 and mempool_size < 50000:
        message = f"🟢 Long Trade Alert 🟢\n\n📈 AI Predicts Rise!\n💰 Best Bid: {best_bid}\n💰 Best Ask: {best_ask}\n🚀 Mempool Size: {mempool_size}\n📊 Sentiment Score: {sentiment_score}\n🔮 AI Prediction: {predicted_price}\n🎯 SL: {stop_loss} | TP: {take_profit}\n\n📢 Action: Enter Long Position!"
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="Markdown")

    else:
        print("No strong trading signal detected.")

# ✅ Run Script
if __name__ == "__main__":
    generate_signal()
