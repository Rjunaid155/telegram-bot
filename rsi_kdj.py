import telebot
import os

# Env se variables
TELEGRAM_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Bot initialize
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Simple message send karna
def send_message():
    message = "Test message from Render hosted bot."
    bot.send_message(CHAT_ID, message)
    print("Message sent successfully!")

if __name__ == "__main__":
    send_message()
