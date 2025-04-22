import os
import requests

# Telegram message bhejnay ka function
def send_telegram_message(message):
    try:
        token = os.getenv("TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")

        if not token or not chat_id:
            print("Telegram token ya chat_id missing hai.")
            return

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
        }
        response = requests.post(url, data=payload)
        print("Telegram response:", response.text)

    except Exception as e:
        print("Telegram message bhejnay me error aaya:", e)

# Main logic
def main():
    print("Script is running...")
    send_telegram_message("Bot started successfully!")
    
    # Yahan tumhara main trading logic ayega
    # Example:
    print("Checking signals...")
    # send_telegram_message("Short signal detected for BTCUSDT. Entry: 60,000")

if __name__ == "__main__":
    main()
