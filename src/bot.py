import os
import random
import time
from datetime import datetime, timedelta
import json
from instagrapi import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="../config/.env")
USERNAME = os.getenv('IG_USERNAME')
PASSWORD = os.getenv('IG_PASSWORD')

# Paths
EXCEPTION_LIST_PATH = "../config/exception_list.txt"
LOG_FILE_PATH = "../logs/followers_log.json"
SESSION_FILE_PATH = "../config/session.json"
CACHE_FILE_PATH = "../config/cache.json"

# Initialize the Instagram client
cl = Client()

def load_exception_list():
    """Load the exception list from a file."""
    if os.path.exists(EXCEPTION_LIST_PATH):
        with open(EXCEPTION_LIST_PATH, 'r') as file:
            return {line.strip().lower() for line in file if line.strip()}
    return set()

def save_log(data):
    """Save log data to a file in JSON format."""
    with open(LOG_FILE_PATH, 'a') as file:
        json.dump(data, file, indent=4)
        file.write('\n')

def get_usernames(user_dict):
    """Extract usernames from a user dictionary."""
    return {user.username.lower() for user in user_dict.values()}

def login():
    """Handle login and session management."""
    if os.path.exists(SESSION_FILE_PATH):
        try:
            cl.load_settings(SESSION_FILE_PATH)
            cl.login(USERNAME, PASSWORD)
            print("[INFO] Session loaded and login successful.")
        except Exception as e:
            print(f"[WARNING] Failed to load session: {e}. Recreating session...")
            cl.set_settings({})
            cl.login(USERNAME, PASSWORD)
            cl.dump_settings(SESSION_FILE_PATH)
            print("[INFO] New session created and saved.")
    else:
        cl.login(USERNAME, PASSWORD)
        cl.dump_settings(SESSION_FILE_PATH)
        print("[INFO] Logged in and session saved.")

def save_cache(data):
    """Save cache data to a file in JSON format."""
    with open(CACHE_FILE_PATH, 'w') as file:
        json.dump(data, file, indent=4)

def load_cache():
    """Load cache data from a file."""
    if os.path.exists(CACHE_FILE_PATH):
        with open(CACHE_FILE_PATH, 'r') as file:
            return json.load(file)
    return {}

def fetch_follow_data():
    """Fetch following and followers data with rate limit handling."""
    try:
        following = cl.user_following(cl.user_id)
        print(f"[SUCCESS] Retrieved {len(following)} following.")
        time.sleep(random.uniform(1, 3))  # Short delay between requests
        followers = cl.user_followers(cl.user_id)
        print(f"[SUCCESS] Retrieved {len(followers)} followers.")
        return following, followers
    except Exception as e:
        print(f"[ERROR] Exception occurred: {e}")
        if 'Please wait a few minutes before you try again' in str(e):
            print("[INFO] Rate limit encountered. Pausing operations.")
            return None, None
        else:
            raise

def unfollow_non_followers():
    """Main function to unfollow non-followers while avoiding detection."""
    # Login and session management
    print("[INFO] Attempting to log in...")
    try:
        login()
    except Exception as e:
        print(f"[ERROR] Login failed: {e}")
        return

    # Load the exception list
    exception_list = load_exception_list()
    print("[INFO] Loaded exception list:", exception_list)

    # Load cache
    cache = load_cache()
    cache_timestamp = cache.get('timestamp')
    following = cache.get('following')
    followers = cache.get('followers')

    if cache_timestamp:
        cache_time = datetime.fromisoformat(cache_timestamp)
        if datetime.now() - cache_time < timedelta(hours=1):
            print("[INFO] Using cached data.")
        else:
            print("[INFO] Cached data is older than 1 hour. Fetching new data.")
            following, followers = fetch_follow_data()
    else:
        print("[INFO] No cache found. Fetching data.")
        following, followers = fetch_follow_data()

    if following is None or followers is None:
        print("[INFO] Could not fetch data due to rate limits. Exiting.")
        return

    # Save fetched data to cache
    cache = {
        'timestamp': datetime.now().isoformat(),
        'following': {user.pk: user.dict() for user in following.values()},
        'followers': {user.pk: user.dict() for user in followers.values()}
    }
    save_cache(cache)

    # Extract usernames
    following_usernames = get_usernames(following)
    follower_usernames = get_usernames(followers)

    # Identify non-followers excluding exceptions
    non_followers = following_usernames - follower_usernames - exception_list
    print(f"[INFO] Identified {len(non_followers)} non-followers.")

    # Log initial state
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'action': 'before_unfollow',
        'following_count': len(following_usernames),
        'follower_count': len(follower_usernames),
        'non_followers_count': len(non_followers),
        'non_followers': list(non_followers)
    }
    save_log(log_data)

    # Unfollow in randomized batches
    non_followers_list = list(non_followers)
    random.shuffle(non_followers_list)
    batch_size = random.randint(3, 7)

    print(f"[INFO] Starting unfollow process in batches of {batch_size}...")

    for i in range(0, len(non_followers_list), batch_size):
        batch = non_followers_list[i:i + batch_size]

        for username in batch:
            try:
                print(f"[INFO] Attempting to unfollow {username}...")
                user_id = cl.user_id_from_username(username)
                cl.user_unfollow(user_id)
                print(f"[SUCCESS] Unfollowed {username}")
                time.sleep(random.uniform(1, 3))  # Short delay between unfollows
            except Exception as e:
                print(f"[ERROR] Error unfollowing {username}: {e}")
                if 'Please wait a few minutes before you try again' in str(e):
                    print("[INFO] Rate limit encountered during unfollow. Pausing operations.")
                    return  # Stop execution on rate limit
                continue  # Skip to the next username if an error occurs

        # Random delay between batches
        sleep_time = random.randint(30, 120)
        print(f"[INFO] Waiting {sleep_time} seconds before next batch...")
        time.sleep(sleep_time)

    print("[INFO] Unfollow process completed.")

    # Log final state
    final_log_data = {
        'timestamp': datetime.now().isoformat(),
        'action': 'after_unfollow',
        'remaining_following': len(following_usernames - non_followers)
    }
    save_log(final_log_data)

# Run the script
if __name__ == "__main__":
    unfollow_non_followers()
