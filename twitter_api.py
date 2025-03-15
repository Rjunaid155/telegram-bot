import os
import tweepy

# Environment variables se keys aur tokens lein
API_KEY = os.getenv('TWITTER_API_KEY')
API_KEY_SECRET = os.getenv('TWITTER_API_KEY_SECRET')
BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')
ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

# Twitter API authentication
auth = tweepy.OAuth1UserHandler(API_KEY, API_KEY_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

# Function to fetch latest tweets based on keyword
def get_latest_tweets(keyword, count=5):
    try:
        tweets = api.search_tweets(q=keyword, count=count, lang='en', result_type='recent')
        return [tweet.text for tweet in tweets]
    except Exception as e:
        print(f"Error fetching tweets: {e}")
        return []

# Test run
if _name_ == '_main_':
    keyword = "Bitcoin"
    tweets = get_latest_tweets(keyword)
    print(f"Latest tweets about {keyword}:")
    for tweet in tweets:
        print(f"- {tweet}")
