import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get your Bearer Token from .env
BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")

# Set headers for auth
headers = {
    "Authorization": f"Bearer {BEARER_TOKEN}"
}

def get_user_id(username):
    url = f"https://api.twitter.com/2/users/by/username/{username}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()["data"]["id"]
    else:
        print(f"Error getting user ID: {response.status_code} - {response.text}")
        return None

def get_recent_tweets2(username, max_results=5):
    user_id = get_user_id(username)
    if not user_id:
        return

    url = f"https://api.twitter.com/2/users/{user_id}/tweets"
    params = {
        "max_results": max_results,
        "tweet.fields": "created_at,text",
        "expansions": "referenced_tweets.id",  # to fetch original tweets
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching tweets: {response.status_code} - {response.text}")


def get_recent_tweets(username, max_results=5):
    user_id = get_user_id(username)
    if not user_id:
        return

    url = f"https://api.twitter.com/2/users/{user_id}/tweets"
    params = {
        "max_results": max_results,
        "tweet.fields": "created_at,text,referenced_tweets",
        "expansions": "referenced_tweets.id",  # to fetch original tweets
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"Error fetching tweets: {response.status_code} - {response.text}")
        return None

    data = response.json()
    original_tweet_lookup = {}
    for tweet in data.get("includes", {}).get("tweets", []):
        original_tweet_lookup[tweet["id"]] = tweet

    # Attach full original tweet text if this is a retweet or quote
    enriched_tweets = []
    for tweet in data.get("data", []):
        full_text = tweet["text"]
        if "referenced_tweets" in tweet:
            for ref in tweet["referenced_tweets"]:
                if ref["type"] == "retweeted":
                    ref_id = ref["id"]
                    full_text = original_tweet_lookup.get(ref_id, {}).get("text", tweet["text"])
        enriched_tweets.append({
            "id": tweet["id"],
            "created_at": tweet["created_at"],
            "text": full_text
        })

    return enriched_tweets


# Example usage
tweets = get_recent_tweets("ProfitsTaken", max_results=20)
for t in tweets:
    print(f"{t['created_at']}: {t['text']}")



# Example usage
# tweets_data = get_recent_tweets("ProfitsTaken", max_results=20)
# if tweets_data:
#     for tweet in tweets_data.get("data", []):
#         print(tweet)  # Full tweet object

