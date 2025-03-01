import requests
import time
import os
import hmac
import base64
from hashlib import sha256

# Bitget API keys from environment variables
API_KEY = os.getenv("BITGET_API_KEY")  
SECRET_KEY = os.getenv("BITGET_SECRET_KEY")  

# Bitget API base URL
BASE_URL = "https://api.bitget.com"

# Function to generate signature
def generate_signature(timestamp, method, request_path, body=''):
    message = f'{timestamp}{method}{request_path}{body}'
    signature = base64.b64encode(
        hmac.new(SECRET_KEY.encode('utf-8'), message.encode('utf-8'), sha256).digest()
    ).decode('utf-8')
    return signature

# Function to fetch market data (BTC, ETH, and altcoins)
def fetch_market_data():
    path = "/api/v2/market/tickers"
    url = BASE_URL + path
    timestamp = str(int(time.time() * 1000))
    
    headers = {
        'ACCESS-KEY': API_KEY,
        'ACCESS-SIGN': generate_signature(timestamp, 'GET', path),
        'ACCESS-TIMESTAMP': timestamp,
        'Content-Type': 'application/json'
    }

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        return data['data']  # Altcoins data
    else:
        print("Error fetching data:", response.text)
        return None

# Test run
if _name_ == "_main_":
    data = fetch_market_data()
    if data:
        print("Fetched Altcoins data:")
        for coin in data[:10]:  # Show top 10 coins data
            print(f"{coin['symbol']}: Last Price: {coin['last']}")
