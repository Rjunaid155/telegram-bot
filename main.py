import telebot  
import os  

TOKEN = os.getenv("TOKEN")
print(f"TOKEN Loaded: {TOKEN}")  # Debugging ke liye

if not TOKEN:
    raise ValueError("Error: TOKEN environment variable is not set!")

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Hello! Yeh mera first Telegram bot hai!")

while True:
    try:
        bot.polling()
    except Exception as e:
        print(f"Error: {e}")  # Yeh error ko print karega instead of crashing
