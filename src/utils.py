"""Helper functions for the project"""

import json
import os

from google.auth import default
from google.auth.credentials import Credentials
from google.auth.exceptions import DefaultCredentialsError
from google.oauth2 import service_account
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import KafkaError, TopicAlreadyExistsError

from src.logger_definition import get_logger

logger = get_logger(__file__)


def create_kafka_topic(
    topic_name: str,
    kafka_server: str = "kafka:9092",
    num_partitions: int = 1,
    replication_factor: int = 1,
) -> None:
    """
    Creates a Kafka topic if it does not already exist.

    Args:
        topic_name (str): Name of the Kafka topic to create.
        kafka_server (str): Kafka server address. Defaults to "kafka:9092".
        num_partitions (int): Number of partitions for the topic. Defaults to 1.
        replication_factor (int): Replication factor for the topic. Defaults to 1.
    """
    admin_client = KafkaAdminClient(
        bootstrap_servers=kafka_server, client_id="reddit_streamer_admin"
    )
    topic = NewTopic(
        name=topic_name, num_partitions=num_partitions, replication_factor=replication_factor
    )
    try:
        admin_client.create_topics([topic])
        logger.info("Topic '%s' created successfully.", topic_name)
    except TopicAlreadyExistsError:
        logger.info("Topic '%s' already exists.", topic_name)
    except KafkaError as e:
        logger.error("Error creating topic '%s': %s", topic_name, e)
    finally:
        admin_client.close()


def load_gcp_credentials() -> Credentials:
    """
    Loads Google Cloud credentials, using Workload Identity on GKE if available,
    or falling back to the GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable for local
    development.

    Returns:
        Credentials: Google Cloud credentials object.
    """
    try:
        # First, try using default credentials (Workload Identity or Application Default)
        credentials, _ = default()
        return credentials

    except DefaultCredentialsError as e:
        # Explicitly re-raise the error with additional context if credentials are not found
        credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        if credentials_json:
            try:
                credentials_dict = json.loads(credentials_json)
                return service_account.Credentials.from_service_account_info(credentials_dict)
            except json.JSONDecodeError as json_error:
                raise ValueError(
                    "Invalid JSON format in GOOGLE_APPLICATION_CREDENTIALS_JSON"
                ) from json_error

        # Raise error if neither method provides valid credentials
        raise OSError(
            "Google Cloud credentials not found. Ensure Workload Identity is enabled on GKE"
            " or set GOOGLE_APPLICATION_CREDENTIALS_JSON locally."
        ) from e
