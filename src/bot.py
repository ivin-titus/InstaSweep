import os
import random
import time
from datetime import datetime
from instagrapi import Client
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="../config/.env")  # Load from config folder
USERNAME = os.getenv('IG_USERNAME')
PASSWORD = os.getenv('IG_PASSWORD')

# Paths
EXCEPTION_LIST_PATH = "../config/exception_list.txt"
LOG_FILE_PATH = "../logs/followers_log.json"

# Initialize the Instagram client
cl = Client()

# Define the device settings
device_settings = {
    "app_version": "165.1.0.20.119",
    "android_version": 27,
    "android_release": "8.1.0",
    "dpi": "480dpi",
    "resolution": "1080x1776",
    "manufacturer": "motorola",
    "device": "Moto G (5S)",
    "model": "montana",
    "cpu": "qcom",
    "version_code": "253447809",
}

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

def unfollow_non_followers():
    """Main function to unfollow non-followers while avoiding detection."""
    
    # Set the device settings
    cl.set_device(device_settings)
    print("[INFO] Device settings configured.")

    # Login to Instagram
    print("[INFO] Attempting to log in...")
    try:
        cl.login(USERNAME, PASSWORD)
        print("[SUCCESS] Login Successful!")
    except Exception as e:
        print(f"[ERROR] Login failed: {e}")
        return

    # Load the exception list
    exception_list = load_exception_list()
    print("[INFO] Loaded exception list:", exception_list)

    # Fetch current following and followers
    print("[INFO] Fetching current following and followers...")

    try:
        following = cl.user_following(cl.user_id)
        print(f"[SUCCESS] Retrieved {len(following)} following.")

        followers = cl.user_followers(cl.user_id)
        print(f"[SUCCESS] Retrieved {len(followers)} followers.")
    except Exception as e:
        print(f"[ERROR] Failed to fetch followers/following: {e}")
        return

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
                time.sleep(random.uniform(5, 10))  # Delay if error occurs
        
        time.sleep(random.uniform(60, 120))  # Longer delay between batches

    # Fetch updated following and followers
    print("[INFO] Fetching updated following and followers...")

    try:
        updated_following = cl.user_following(cl.user_id)
        updated_followers = cl.user_followers(cl.user_id)
        print(f"[SUCCESS] Updated counts - Following: {len(updated_following)}, Followers: {len(updated_followers)}")
    except Exception as e:
        print(f"[ERROR] Failed to fetch updated followers/following: {e}")
        return

    # Extract updated usernames
    updated_following_usernames = get_usernames(updated_following)
    updated_follower_usernames = get_usernames(updated_followers)

    # Log final state
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'action': 'after_unfollow',
        'following_count': len(updated_following_usernames),
        'follower_count': len(updated_follower_usernames)
    }
    save_log(log_data)

    print("[SUCCESS] Unfollow process completed!")

if __name__ == "__main__":
    unfollow_non_followers()
