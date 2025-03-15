import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from twitter_api import get_latest_tweets

# NLTK resources download
nltk.download('vader_lexicon')

# Initialize sentiment analyzer
sia = SentimentIntensityAnalyzer()

# Function to analyze sentiment of tweets
def analyze_sentiment(keyword, count=5):
    tweets = get_latest_tweets(keyword, count)
    results = []
    
    for tweet in tweets:
        score = sia.polarity_scores(tweet)
        sentiment = 'Neutral'
        if score['compound'] > 0.05:
            sentiment = 'Positive'
        elif score['compound'] < -0.05:
            sentiment = 'Negative'
        
        results.append({'tweet': tweet, 'sentiment': sentiment, 'score': score['compound']})
    
    return results

# Test run
if __name__ == '__main__':
    keyword = "Bitcoin"
    results = analyze_sentiment(keyword)
    for res in results:
        print(f"Tweet: {res['tweet']}\nSentiment: {res['sentiment']} (Score: {res['score']})\n")
