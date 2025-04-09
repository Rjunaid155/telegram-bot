import requests

Telegram_token = "TOKEN"
chat_id = "YOUR_CHAT_ID"
message = "Test alert from MEXC bot — working perfectly!"

url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
data = {
    "chat_id": chat_id,
    "text": message
}

response = requests.post(url, data=data)
print(response.status_code)
print(response.text)
