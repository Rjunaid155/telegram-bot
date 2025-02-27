import telebot  
import os  

# Bot Token ko environment variable se lene ka tareeqa  
TOKEN = os.getenv("8094066627:AAFvUUyhSivGyp6yphOkhTbj6gjJGzFS73U")  

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Hello! Yeh mera first Telegram bot hai!")

bot.polling()
