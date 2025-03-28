import os
import schedule
import time
import requests
import smtplib
from email.mime.text import MIMEText
Load environment variables
BITGET_API_KEY = os.getenv("BITGET_API_KEY") BITGET_SECRET_KEY = os.getenv("BITGET_SECRET_KEY") MEXC_API_KEY = os.getenv("MEXC_API_KEY") MEXC_SECRET_KEY = os.getenv("MEXC_SECRET_KEY") EMAIL = os.getenv("EMAIL") EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

Function to check spike moves

def check_spike_moves(): print("Checking for spike moves...") try: # Example request to fetch market data (Replace with actual API call) response = requests.get("https://api.mexc.com/api/v3/ticker/price") data = response.json()

# Example logic: Just logging price data
    for item in data:
        print(f"Symbol: {item['symbol']}, Price: {item['price']}")

    # Send an email alert (Dummy logic, update with real conditions)
    send_email_alert("Spike detected! Check the market.")
except Exception as e:
    print(f"Error checking spike moves: {e}")

Function to send email alerts

def send_email_alert(message): try: msg = MIMEText(message) msg["Subject"] = "Spike Alert" msg["From"] = EMAIL msg["To"] = EMAIL

server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL, EMAIL_PASSWORD)
    server.sendmail(EMAIL, EMAIL, msg.as_string())
    server.quit()
    
    print("Email alert sent successfully!")
except Exception as e:
    print(f"Error sending email: {e}")

Schedule the function to run every 3 minutes

schedule.every(3).minutes.do(check_spike_moves)

Keep the script running

while True: schedule.run_pending() time.sleep(10)
