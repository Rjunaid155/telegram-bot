import requests
import os

def send_telegram_message(message):
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message
    }
    response = requests.post(url, data=data)
    print(response.status_code)
    print(response.text)

# Test message
send_telegram_message("Test alert from MEXC bot – working perfectly!")
