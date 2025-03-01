import requests
import time
import os
import hmac
import hashlib
import base64

# ✅ Bitget API keys (Render ke environment variables se)
API_KEY = os.getenv("BG_API_KEY")
SECRET_KEY = os.getenv("BG_SECRET_KEY")
PASSPHRASE = os.getenv("BG_PASSPHRASE")  

# ✅ Bitget API ka base URL
BASE_URL = "https://api.bitget.com"

# ✅ Signature generate karne ka function
def generate_signature(timestamp, method, request_path, body=""):
    message = f"{timestamp}{method}{request_path}{body}"
    signature = hmac.new(SECRET_KEY.encode(), message.encode(), hashlib.sha256).digest()
    return base64.b64encode(signature).decode()

# ✅ Order book data fetch karne ka function
def fetch_order_book(symbol="BTCUSDT"):
    path = f"/api/v2/market/orderbook?symbol={symbol}&limit=10"
    url = BASE_URL + path
    timestamp = str(int(time.time() * 1000))
    
    headers = {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": generate_signature(timestamp, "GET", path),
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": PASSPHRASE,
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.text}")
        return None

# ✅ Test run
if _name_ == "_main_":
    order_book = fetch_order_book("BTCUSDT")
    if order_book:
        print("Order Book Data:", order_book)
