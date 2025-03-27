import requests
import smtplib
import schedule
import time
from config import BITGET_API_KEY, BITGET_SECRET_KEY, MEXC_API_KEY, MEXC_SECRET_KEY, EMAIL, EMAIL_PASSWORD

# Function to get price data from Bitget
def get_bitget_data():
    url = "https://api.bitget.com/api/v2/market/tickers"
    headers = {"X-Bitget-API-Key": BITGET_API_KEY}
    response = requests.get(url, headers=headers)
    data = response.json()
    
    spike_coins = []
    for coin in data['data']:
        symbol = coin['symbol']
        change = float(coin['change'])  # Price change percentage
        if abs(change) >= 3:  # 3% spike move
            spike_coins.append((symbol, change, "Bitget"))
    
    return spike_coins

# Function to get price data from MEXC
def get_mexc_data():
    url = "https://api.mexc.com/api/v3/ticker/24hr"
    response = requests.get(url)
    data = response.json()
    
    spike_coins = []
    for coin in data:
        symbol = coin['symbol']
        change = float(coin['priceChangePercent'])  # Price change percentage
        if abs(change) >= 3:  # 3% spike move
            spike_coins.append((symbol, change, "MEXC"))
    
    return spike_coins

# Function to send email alert
def send_email_alert(spike_moves):
    if not spike_moves:
        return
    
    subject = "Spike Move Alert 🚀"
    body = "These coins have made a big move:\n\n"
    
    for coin, change, exchange in spike_moves:
        direction = "Long" if change > 0 else "Short"
        body += f"{coin} ({exchange}): {direction} | {change}%\n"
    
    body += "\nTrade carefully!"
    
    message = f"Subject: {subject}\n\n{body}"
    
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL, EMAIL_PASSWORD)
        server.sendmail(EMAIL, EMAIL, message)

# Function to check for spike moves
def check_spike_moves():
    bitget_spikes = get_bitget_data()
    mexc_spikes = get_mexc_data()
    
    all_spikes = bitget_spikes + mexc_spikes
    send_email_alert(all_spikes)

# Schedule the script to run every 3 minutes
schedule.every(3).minutes.do(check_spike_moves)

# Keep the script running
while True:
    schedule.run_pending()
    time.sleep(10)
