# %%
import json
import os
import time

import praw

from src.constants import DATA_RAW


# %%
class RedditStreamer:
    """
    A class to handle pseudo-streaming of Reddit posts based on specific tags.
    """

    def __init__(
        self,
        subreddit,
        query_tags,
        save_dir=DATA_RAW,
        secrets_path=".secrets/reddit_credentials.json",
    ):
        """
        Initializes the RedditStreamer with API credentials loaded from a JSON file,
        along with the subreddit and tags to search for.

        Args:
            subreddit (str): The subreddit to fetch posts from.
            query_tags (list of str): Tags to filter posts by in their titles.
            save_dir (str): Directory where posts will be saved.
            secrets_path (str): Path to the JSON file with Reddit API credentials.
        """
        credentials = self._load_credentials(secrets_path)
        self.reddit = praw.Reddit(
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"],
            user_agent=credentials["user_agent"],
        )
        self.subreddit = subreddit
        self.query_tags = query_tags
        self.save_dir = save_dir
        self._ensure_directory_exists(save_dir)

    def _load_credentials(self, path):
        """
        Loads Reddit API credentials from a JSON file.

        Args:
            path (str): Path to the JSON file with Reddit API credentials.

        Returns:
            dict: A dictionary containing Reddit API credentials.
        """
        with open(path, "r") as f:
            return json.load(f)

    def _ensure_directory_exists(self, directory):
        """
        Ensures that the specified directory exists, creating it if necessary.

        Args:
            directory (str): Path to the directory to check or create.
        """
        if not os.path.exists(directory):
            os.makedirs(directory)

    def fetch_posts(self, limit=10):
        """
        Fetches posts from the subreddit that contain specified tags in their titles.

        Args:
            limit (int): The maximum number of posts to retrieve in each fetch.

        Returns:
            list of dict: A list of posts matching the tags, formatted as dictionaries.
        """
        subreddit = self.reddit.subreddit(self.subreddit)
        filtered_posts = []

        for submission in subreddit.new(limit=limit):
            if any(tag.lower() in submission.title.lower() for tag in self.query_tags):
                post = {
                    "id": submission.id,
                    "title": submission.title,
                    "score": submission.score,
                    "url": submission.url,
                    "created_utc": submission.created_utc,
                }
                filtered_posts.append(post)

        return filtered_posts

    def save_post(self, post):
        """
        Saves a single post to a JSON file named with the post ID.

        Args:
            post (dict): The post data to save.
        """
        filename = os.path.join(self.save_dir, f"{post['id']}.json")
        with open(filename, "w") as f:
            json.dump(post, f)
        print(f"Saved post {post['id']} to {filename}")

    def save_posts(self, posts):
        """
        Saves each post in the list to a separate JSON file.

        Args:
            posts (list of dict): The posts to save.
        """
        for post in posts:
            self.save_post(post)

    def start_streaming(self, interval=60, limit=10):
        """
        Starts the pseudo-streaming process that periodically fetches and saves posts.

        Args:
            interval (int): Time interval (in seconds) between each fetch cycle.
            limit (int): The maximum number of posts to fetch in each cycle.
        """
        while True:
            print(f"Fetching posts from r/{self.subreddit}...")
            posts = self.fetch_posts(limit=limit)
            self.save_posts(posts)
            print(f"Saved {len(posts)} posts. Sleeping for {interval} seconds...")
            time.sleep(interval)


# %%
streamer = RedditStreamer(subreddit="all", query_tags=["android", "ios"])
streamer.start_streaming(interval=2, limit=100)
# %%
