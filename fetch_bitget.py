import requests
import json
import time
import praw
import nltk
import os
from nltk.sentiment import SentimentIntensityAnalyzer

# NLTK Sentiment Analyzer
nltk.download('vader_lexicon')
sia = SentimentIntensityAnalyzer()

# Load API Credentials from Environment Variables
TELEGRAM_TOKEN = os.getenv("TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BITGET_ORDER_BOOK_URL = "https://api.bitget.com/api/v2/spot/market/orderbook?symbol=BTCUSDT"
MEMPOOL_URL = "https://mempool.space/api/mempool"

# Reddit API Credentials (from environment variables)
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

# Function to fetch Bitget order book data
def get_bitget_order_book():
    try:
        response = requests.get(BITGET_ORDER_BOOK_URL)
        data = response.json()
        return data
    except Exception as e:
        print(f"Error fetching Bitget Order Book: {e}")
        return None

# Function to fetch Mempool.space data
def get_mempool_data():
    try:
        response = requests.get(MEMPOOL_URL)
        data = response.json()
        return data
    except Exception as e:
        print(f"Error fetching Mempool Data: {e}")
        return None

# Function to analyze Reddit sentiment
def analyze_reddit_sentiment(subreddit_name, keyword, limit=10):
    subreddit = reddit.subreddit(subreddit_name)
    sentiment_scores = []

    for post in subreddit.search(keyword, limit=limit):
        score = sia.polarity_scores(post.title)
        sentiment_scores.append(score["compound"])

    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
    return avg_sentiment

# Function to send Telegram alerts
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    response = requests.post(url, data=data)
    return response.json()

# Main function to fetch data and analyze signals
def main():
    print("Fetching data...")

    # Get Bitget Order Book Data
    order_book = get_bitget_order_book()
    if order_book and "data" in order_book:
        best_bid = float(order_book["data"]["bids"][0][0])
        best_ask = float(order_book["data"]["asks"][0][0])
    else:
        best_bid, best_ask = None, None

    # Get Mempool Data
    mempool_data = get_mempool_data()
   mempool_size = mempool_data.get("vsize", None)  # "size" ki jagah "vsize"

    # Get Reddit Sentiment Score
    reddit_sentiment = analyze_reddit_sentiment("cryptocurrency", "Bitcoin")

    # Decision Making
    if best_bid and best_ask and mempool_size:
        if reddit_sentiment < -0.3 and mempool_size > 100000:
            message = f"🔴 *Short Trade Alert* 🔴\n\n📉 Bitcoin Short Signal Detected!\n\n💰 Best Bid: {best_bid}\n💰 Best Ask: {best_ask}\n🚀 Mempool Size: {mempool_size}\n📊 Reddit Sentiment: {reddit_sentiment}\n\n📢 *Action:* Strong Short Signal!"
            send_telegram_alert(message)
        else:
            print("No strong short signal detected.")

if __name__ == "__main__":
    main()
