import time
import requests

# Bitget API endpoint for fetching candles
url = "https://api.bitget.com/api/mix/v1/market/candles"

# Correct time formatting (milliseconds)
end_time = int(time.time() * 1000)
start_time = end_time - (60 * 60 * 1000)  # 1 hour ago

# Test with a valid symbol
params = {
    "symbol": "BTCUSDT_UMCBL",  # Ensure it's correct
    "granularity": "300",        # 5-minute candles
    "startTime": str(start_time),
    "endTime": str(end_time),
    "limit": "100"               # Limit candles count
}

# Send GET request to Bitget API
response = requests.get(url, params=params)
print("Response status code:", response.status_code)
print("Response text:", response.text)

# Check if JSON response contains error code
try:
    data = response.json()
    if "code" in data and data["code"] != "00000":
        print("Error:", data["msg"])
    else:
        print("Candles data:", data)
except ValueError:
    print("Invalid JSON response")
