import requests
import time
import os
from hashlib import sha256
import hmac
import base64

# Bitget API keys from environment variables (Render pe set karenge)
API_KEY = os.getenv(bg_ba1f5af3d37b7e78f859fab0fd506920)
SECRET_KEY = os.getenv(69115b5edde54773da5805ab6714d88771151e537333f1d587d861a628039c7a)

# Bitget API ka base URL
BASE_url = "https://api.bitget.com/api/v2/public/time"

# Function to generate signature
def generate_signature(timestamp, method, request_path, body=''):
    message = f'{timestamp}{method}{request_path}{body}'
    signature = hmac.new(SECRET_KEY.encode('utf-8'), message.encode('utf-8'), sha256).digest()
    return base64.b64encode(signature).decode('utf-8')

# Function to fetch market data (BTC, ETH, and altcoins)
def fetch_market_data():
    path = "/market/tickers"
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
