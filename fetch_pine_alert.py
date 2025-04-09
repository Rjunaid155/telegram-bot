import requests
import os

# Get token and chat ID from environment variables
bot_token = os.environ.get("TELEGRAM_TOKEN")
chat_id = os.environ.get("TELEGRAM_CHAT_ID")

message = "Test alert from MEXC bot - working perfectly!"

url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
data = {
    "chat_id": chat_id,
    "text": message
}

response = requests.post(url, data=data)
print(response.status_code)
print(response.text)
