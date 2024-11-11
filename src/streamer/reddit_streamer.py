import argparse
import json
import os
import time

import praw
from kafka import KafkaProducer

from src.constants import DATA_COMMENTS, DATA_POSTS, SECRETS, STREAMER_TAGS
from src.logger_definition import get_logger
from src.utils import create_kafka_topic

logger = get_logger(__file__)


class RedditCommentStreamer:
    """
    A class to stream new posts and comments on Reddit that match specific tags.
    """

    def __init__(
        self,
        subreddit: str,
        query_tags: list[str],
        post_save_dir: str,
        comment_save_dir: str,
        secrets_path: str,
        kafka_server: str,
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
            kafka_server(str): Kafka server address.
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
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=kafka_server, value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )

        self._ensure_directory_exists(post_save_dir)
        self._ensure_directory_exists(comment_save_dir)

        for tag in self.query_tags:
            create_kafka_topic(tag)

    def _load_credentials(self, path: str) -> dict:
        """
        Loads Reddit API credentials from a JSON file.

        Args:
            path (str): Path to the JSON file with Reddit API credentials.

        Returns:
            dict: A dictionary containing Reddit API credentials.
        """
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _ensure_directory_exists(self, directory: str):
        """
        Ensures that the specified directory exists, creating it if necessary.

        Args:
            directory (str): Path to the directory to check or create.
        """
        if not os.path.exists(directory):
            os.makedirs(directory)

    def fetch_and_save_matching_posts(self, limit: int = 100):
        """
        Fetches recent posts from the subreddit that contain specified tags in their titles or
        flairs, saves them, and updates the tracked_post_ids set.

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

    def save_post(self, post: dict, tag: str):
        """
        Saves a single post to a JSON file named with the post ID and tag, and sends it to Kafka.

        Args:
            post (dict): The post data to save.
            tag (str): The tag that matched this post.
        """
        filename = os.path.join(self.post_save_dir, f"{tag}_{post['id']}.json")

        # Save the post to JSON
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(post, f)
        logger.info("Saved post %s with tag '%s' to %s", post["id"], tag, filename)

        # Prepare a subset of the post data for Kafka
        kafka_data = {
            "tag": tag,
            "id": post["id"],
            "created_utc": post["created_utc"],
            "text": post["title"],  # Rename "title" to "text" for Kafka
        }
        # Send the transformed post data to a Kafka topic named after the tag
        self.kafka_producer.send(tag, kafka_data)
        logger.info("Sent post %s to Kafka topic '%s'", post["id"], tag)

    def save_comment(self, comment: dict, tag: str):
        """
        Saves a single comment to a JSON file named with the comment ID and tag, and sends it to
        Kafka.

        Args:
            comment (dict): The comment data to save.
            tag (str): The tag associated with the post this comment belongs to.
        """
        # Skip if author is "AutoModerator"
        if comment.get("author") == "AutoModerator":
            logger.info("Skipping comment %s by AutoModerator", comment["id"])
            return

        filename = os.path.join(self.comment_save_dir, f"{tag}_{comment['id']}.json")

        # Save the comment to JSON
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(comment, f)
        logger.info("Saved comment %s with tag '%s' to %s", comment["id"], tag, filename)

        # Prepare a subset of the comment data for Kafka
        kafka_data = {
            "tag": tag,
            "id": comment["id"],
            "created_utc": comment["created_utc"],
            "text": comment["body"],  # Rename "body" to "text" for Kafka
        }
        # Send the transformed comment data to a Kafka topic named after the tag
        self.kafka_producer.send(tag, kafka_data)
        logger.info("Sent comment %s to Kafka topic '%s'", comment["id"], tag)

    def start_streaming(self, interval: int = 2):
        """
        Starts streaming new posts and comments, saving only those matching the specified tags.

        Args:
            interval (int): Time interval (in seconds) to refresh tracked posts.
        """
        # Initial fetch of posts matching the query tags
        logger.info("Starting stream...")
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
                logger.info("Refreshing tracked posts...")
                self.fetch_and_save_matching_posts()

    def close(self):
        """Ensure all messages are sent and shuts down the Kafka producer."""
        self.kafka_producer.flush()
        self.kafka_producer.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Stream new posts and comments on Reddit that match specified tags."
    )
    parser.add_argument(
        "--subreddit", type=str, default="all", help="Subreddit to monitor (default: all)"
    )
    parser.add_argument(
        "--query_tags", nargs="+", default=STREAMER_TAGS, help="List of tags to filter posts by"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=2,
        help="Time interval in seconds to refresh tracked posts (default: 300)",
    )
    parser.add_argument(
        "--post_save_dir",
        type=str,
        default=DATA_POSTS,
        help="Directory to save matching posts",
    )
    parser.add_argument(
        "--comment_save_dir",
        type=str,
        default=DATA_COMMENTS,
        help="Directory to save matching comments",
    )
    parser.add_argument(
        "--secrets_path",
        type=str,
        default=SECRETS / "reddit_credentials.json",
        help="Path to the JSON file with Reddit API credentials",
    )

    parser.add_argument(
        "--kafka_server",
        type=str,
        default=os.getenv("KAFKA_SERVER", "kafka:9092"),
        help="Kafka server address (default: kafka:9092)",
    )

    args = parser.parse_args()

    streamer = RedditCommentStreamer(
        subreddit=args.subreddit,
        query_tags=args.query_tags,
        post_save_dir=args.post_save_dir,
        comment_save_dir=args.comment_save_dir,
        secrets_path=args.secrets_path,
        kafka_server=args.kafka_server,
    )
    try:
        streamer.start_streaming(interval=args.interval)
    finally:
        streamer.close()  # Ensure Kafka producer closes cleanly
