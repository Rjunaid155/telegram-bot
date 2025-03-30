import requests
import time
from telegram import Bot

MEXC API Endpoint for order book and market data

MEXC_ORDER_BOOK_URL = "https://api.mexc.com/api/v3/depth" 
MEXC_TICKER_URL = "https://api.mexc.com/api/v3/ticker/price"

Telegram Bot Setup

TELEGRAM_BOT_TOKEN = "Token"
TELEGRAM_CHAT_ID = "your_chat_id" 
bot = Bot(token=TELEGRAM_BOT_TOKEN)

def fetch_order_book(symbol): 
params = {"symbol": symbol, "limit": 50}  # Fetch top 50 orders
response = requests.get(MEXC_ORDER_BOOK_URL, params=params) 
if response.status_code == 200:
return response.json() 
return None

def fetch_price(symbol): 
params = {"symbol": symbol} 
response = requests.get(MEXC_TICKER_URL, params=params) 
if response.status_code == 200: 
return float(response.json()["price"]) 
return None

def analyze_trade(symbol): 
order_book = fetch_order_book(symbol) 
if not order_book: 
return None

bids = order_book["bids"]  # Buy orders
asks = order_book["asks"]  # Sell orders

if not bids or not asks:
    return None

highest_bid = float(bids[0][0])
lowest_ask = float(asks[0][0])
spread = abs(highest_bid - lowest_ask)

if spread > 0.5 * highest_bid / 100:  # Large spread, possible move
    direction = "Short" if highest_bid > lowest_ask else "Long"
    expected_move = round(spread / highest_bid * 100, 2)  # % move prediction
    return symbol, direction, highest_bid, expected_move

return None

def send_signal(symbol, direction, entry_price, expected_move):
message = (f"🚀 Trade Alert 🚀\n"
           f"🔹 Coin: {symbol}\n" 
           f"📉 Trade Type: {direction}\n" 
           f"💰 Entry Price: {entry_price}\n" 
           f"📊 Expected Move: {expected_move}%\n") 
bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="Markdown")

def main(): altcoins = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"]  # Add more as needed 
while True:
for coin in altcoins: 
trade_signal = analyze_trade(coin) 
if trade_signal:
send_signal(*trade_signal) 
time.sleep(60)  # Check every 1 min

if __name__ == "__main__": 
main()
