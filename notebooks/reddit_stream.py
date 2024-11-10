# %%
import json
import os
import time

import praw

from src.constants import DATA_COMMENTS, DATA_POSTS, SECRETS


# %%
class RedditCommentStreamer:
    """
    A class to stream new posts and comments on Reddit that match specific tags.
    """

    def __init__(
        self,
        subreddit,
        query_tags,
        post_save_dir=DATA_POSTS,
        comment_save_dir=DATA_COMMENTS,
        secrets_path=SECRETS / "reddit_credentials.json",
    ):
        """
        Initializes the RedditCommentStreamer with API credentials loaded from a JSON file,
        and sets the subreddit and tags to search for.

        Args:
            subreddit (str): The subreddit to monitor for posts and comments.
            query_tags (list of str): Tags to filter posts by in their titles or flairs.
            post_save_dir (str): Directory where matching posts will be saved.
            comment_save_dir (str): Directory where matching comments will be saved.
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
        self.post_save_dir = post_save_dir
        self.comment_save_dir = comment_save_dir
        self.tracked_post_ids = {}  # Maps post IDs to their matching tags
        self._ensure_directory_exists(post_save_dir)
        self._ensure_directory_exists(comment_save_dir)

    def _load_credentials(self, path):
        """
        Loads Reddit API credentials from a JSON file.

        Args:
            path (str): Path to the JSON file with Reddit API credentials.

        Returns:
            dict: A dictionary containing Reddit API credentials.
        """
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _ensure_directory_exists(self, directory):
        """
        Ensures that the specified directory exists, creating it if necessary.

        Args:
            directory (str): Path to the directory to check or create.
        """
        if not os.path.exists(directory):
            os.makedirs(directory)

    def fetch_and_save_matching_posts(self, limit=50):
        """
        Fetches recent posts from the subreddit that contain specified tags in their titles or flairs,
        saves them, and updates the tracked_post_ids set.

        Args:
            limit (int): The maximum number of posts to retrieve in each fetch.
        """
        subreddit = self.reddit.subreddit(self.subreddit)

        for submission in subreddit.new(limit=limit):
            # Find the matching tag
            matching_tag = next(
                (tag for tag in self.query_tags if tag.lower() in submission.title.lower()), None
            )
            if not matching_tag and submission.link_flair_text:
                matching_tag = (
                    submission.link_flair_text.lower()
                    if submission.link_flair_text.lower()
                    in [tag.lower() for tag in self.query_tags]
                    else None
                )

            # Save post details if it matches a tag and hasn't been saved yet
            if matching_tag and submission.id not in self.tracked_post_ids:
                post_data = {
                    "id": submission.id,
                    "title": submission.title,
                    "selftext": submission.selftext,
                    "flair": submission.link_flair_text,
                    "score": submission.score,
                    "url": submission.url,
                    "created_utc": submission.created_utc,
                    "tag": matching_tag,
                }
                self.save_post(post_data, matching_tag)
                self.tracked_post_ids[submission.id] = matching_tag

    def save_post(self, post, tag):
        """
        Saves a single post to a JSON file named with the post ID and tag.

        Args:
            post (dict): The post data to save.
            tag (str): The tag that matched this post.
        """
        filename = os.path.join(self.post_save_dir, f"{tag}_{post['id']}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(post, f)
        print(f"Saved post {post['id']} with tag '{tag}' to {filename}")

    def save_comment(self, comment, tag):
        """
        Saves a single comment to a JSON file named with the comment ID and tag.

        Args:
            comment (dict): The comment data to save.
            tag (str): The tag associated with the post this comment belongs to.
        """
        filename = os.path.join(self.comment_save_dir, f"{tag}_{comment['id']}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(comment, f)
        print(f"Saved comment {comment['id']} with tag '{tag}' to {filename}")

    def start_streaming(self, interval=60):
        """
        Starts streaming new posts and comments, saving only those matching the specified tags.

        Args:
            interval (int): Time interval (in seconds) to refresh tracked posts.
        """
        # Initial fetch of posts matching the query tags
        self.fetch_and_save_matching_posts()

        # Stream comments and filter based on tracked posts
        for comment in self.reddit.subreddit("all").stream.comments(skip_existing=True):
            post_id = comment.submission.id
            if post_id in self.tracked_post_ids:
                tag = self.tracked_post_ids[post_id]
                comment_data = {
                    "id": comment.id,
                    "post_id": post_id,
                    "author": str(comment.author),
                    "body": comment.body,
                    "score": comment.score,
                    "created_utc": comment.created_utc,
                    "tag": tag,
                }
                self.save_comment(comment_data, tag)

            # Refresh tracked posts periodically
            if time.time() % interval < 1:
                print("Refreshing tracked posts...")
                self.fetch_and_save_matching_posts()


# %%
streamer = RedditCommentStreamer(
    subreddit="all", query_tags=["trump", "donaldtrump", "kamala", "kamalaharris"]
)
streamer.start_streaming(interval=2)

# %%
