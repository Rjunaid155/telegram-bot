import requests
import time

# Maximum retries if a request fails
MAX_RETRIES = 3

# Fetch candles with retries
def fetch_candles(symbol, interval="15m", limit=100):
    url = "https://api.bitget.com/api/mix/v1/market/candles"
    params = {"symbol": symbol, "granularity": interval, "limit": limit}
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and "data" in data:
                    return data["data"]
                else:
                    print("Unexpected response format:", data)
                    return None
            else:
                print("Error fetching candles:", response.text)
        except requests.exceptions.RequestException as e:
            print(f"Request failed (attempt {attempt + 1}/{MAX_RETRIES}):", e)
        
        time.sleep(2)  # Retry after a short delay

    return None

# Monitor coins with retries
def monitor_all_coins():
    url = "https://api.bitget.com/api/mix/v1/market/contracts?productType=umcbl"
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                coins = [pair["symbol"] for pair in response.json().get("data", [])]
                for coin in coins:
                    detect_short_trade(coin)
                break  # Exit loop if successful
            else:
                print("Error fetching coins:", response.text)
        except requests.exceptions.RequestException as e:
            print(f"Request failed (attempt {attempt + 1}/{MAX_RETRIES}):", e)
        
        time.sleep(2)  # Retry delay
