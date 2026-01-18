from .base import SearchProvider
from datetime import datetime
import tweepy

class TwitterProvider(SearchProvider):
    def __init__(self, api_key=None):
        self.client = None
        if api_key and api_key != "YOUR_TWITTER_BEARER_TOKEN":
            try:
                self.client = tweepy.Client(bearer_token=api_key)
            except Exception as e:
                print(f"[Twitter] Init Error: {e}")

    def search(self, query, count=10):
        if not self.client:
            print(f"[Twitter] No valid API key. Skipping search for '{query}'")
            return []

        print(f"[Twitter] Searching for: {query}")
        try:
            # Search recent tweets (requires Basic or Pro tier for comprehensive access, Free is very limited)
            response = self.client.search_recent_tweets(
                query=f"{query} -is:retweet lang:en",
                max_results=min(count, 100),
                tweet_fields=['created_at', 'author_id', 'text']
            )
            
            if not response.data:
                return []

            results = []
            for tweet in response.data:
                results.append({
                    "platform": "Twitter",
                    "post_id": str(tweet.id),
                    "post_text": tweet.text,
                    "username": str(tweet.author_id), # Requires user expansion to get handle
                    "profile_url": f"https://twitter.com/i/user/{tweet.author_id}",
                    "timestamp": tweet.created_at or datetime.now()
                })
            return results

        except Exception as e:
            # Re-raise so scheduler can handle rate limits logic
            error_str = str(e)
            if "429" in error_str:
                raise Exception(f"429 Too Many Requests - Rate Limit Exceeded")
            
            print(f"[Twitter] Error: {e}")
            return []
