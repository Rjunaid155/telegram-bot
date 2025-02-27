import telebot  
import os  

# Token ko environment variable se sahi tareeke se lena
TOKEN = os.getenv(8094066627:AAFvUUyhSivGyp6yphOkhTbj6gjJGzFS73U)

# Token check karne ke liye
if not TOKEN:
    print("Error: Token not found. Make sure you set the TOKEN environment variable.")
    exit(1)

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Hello! Yeh mera first Telegram bot hai!")

bot.polling()
