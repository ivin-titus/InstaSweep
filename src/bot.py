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

def load_exception_list():
    """Load the exception list from a file."""
    if os.path.exists(EXCEPTION_LIST_PATH):
        with open(EXCEPTION_LIST_PATH, 'r') as file:
            return {line.strip().lower() for line in file if line.strip()}
    return set()

def save_log(data):
    """Save log data to a file in JSON format."""
    with open(LOG_FILE_PATH, 'a') as file:
        json.dump(data, file)
        file.write('\n')

def get_usernames(user_dict):
    """Extract usernames from a user dictionary."""
    return {user.username.lower() for user in user_dict.values()}

def unfollow_non_followers():
    """Main function to unfollow non-followers while avoiding detection."""
    
    # Login to Instagram
    cl.login(USERNAME, PASSWORD)
    print("Login Successful!")

    # Load the exception list
    exception_list = load_exception_list()
    print("Loaded exception list:", exception_list)

    # Fetch current following and followers
    following = cl.user_following(cl.user_id)
    followers = cl.user_followers(cl.user_id)

    # Extract usernames
    following_usernames = get_usernames(following)
    follower_usernames = get_usernames(followers)

    # Identify non-followers excluding exceptions
    non_followers = following_usernames - follower_usernames - exception_list

    # Log initial state
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'action': 'before_unfollow',
        'following_count': len(following_usernames),
        'follower_count': len(follower_usernames),
        'following_usernames': list(following_usernames),
        'follower_usernames': list(follower_usernames)
    }
    save_log(log_data)

    # Unfollow in randomized batches
    non_followers_list = list(non_followers)
    random.shuffle(non_followers_list)
    batch_size = random.randint(3, 7)
    
    for i in range(0, len(non_followers_list), batch_size):
        batch = non_followers_list[i:i + batch_size]
        
        for username in batch:
            try:
                user_id = cl.user_id_from_username(username)
                cl.user_unfollow(user_id)
                print(f"Unfollowed {username}")
                
                time.sleep(random.uniform(1, 3))  # Short delay between unfollows
            except Exception as e:
                print(f"Error unfollowing {username}: {e}")
                time.sleep(random.uniform(5, 10))  # Delay if error occurs
        
        time.sleep(random.uniform(60, 120))  # Longer delay between batches

    # Fetch updated following and followers
    updated_following = cl.user_following(cl.user_id)
    updated_followers = cl.user_followers(cl.user_id)

    # Extract updated usernames
    updated_following_usernames = get_usernames(updated_following)
    updated_follower_usernames = get_usernames(updated_followers)

    # Log final state
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'action': 'after_unfollow',
        'following_count': len(updated_following_usernames),
        'follower_count': len(updated_follower_usernames),
        'following_usernames': list(updated_following_usernames),
        'follower_usernames': list(updated_follower_usernames)
    }
    save_log(log_data)

    print("Unfollow process completed!")

if __name__ == "__main__":
    unfollow_non_followers()
