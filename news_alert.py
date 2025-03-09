import os
import smtplib
import requests
import telebot
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Environment Variables Load karna
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")
TELEGRAM_BOT_TOKEN = os.getenv("TOKEN-2")  # New bot ka token use ho raha hai
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Telegram Bot Initialize karna
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# News Fetch Karne Ka Function
def get_latest_news():
    url = f"https://newsdata.io/api/1/news?apikey={NEWS_API_KEY}&q=crypto&language=en"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if "results" in data and len(data["results"]) > 0:
            return data["results"][0]  # Sabse latest news
    return None

# Market Impact Analysis (Simple Logic - Improve Kar Sakte Ho)
def analyze_impact(title):
    title_lower = title.lower()
    if "rise" in title_lower or "bullish" in title_lower or "gain" in title_lower:
        return "Positive 🔼"
    elif "fall" in title_lower or "bearish" in title_lower or "loss" in title_lower:
        return "Negative 🔽"
    else:
        return "Neutral ➖"

# Email Send Karne Ka Function
def send_email(subject, body):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = TO_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USER, TO_EMAIL, msg.as_string())
        server.quit()
        print("Email Sent Successfully!")
    except Exception as e:
        print("Email Sending Error:", str(e))

# Telegram Message Send Karne Ka Function
def send_telegram_message(message):
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        print("Telegram Alert Sent!")
    except Exception as e:
        print("Telegram Error:", str(e))

# Main Execution
news = get_latest_news()
if news:
    title = news["title"]
    link = news["link"]
    impact = analyze_impact(title)
    
    # *Roman Urdu Description Generate Karna*
    roman_urdu_description = f"Aik naye khabar mili hai: {title}. Yeh market ka impact {impact} lagta hai. Tafseelat ke liye yeh dekhein: {link}"
    
    # *Email Alert*
    send_email("Crypto News Alert!", roman_urdu_description)
    
    # *Telegram Alert (Agar auto chal sakay to)*
    send_telegram_message(roman_urdu_description)

else:
    print("Koi naye crypto news nahi mili.")
