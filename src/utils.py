"""Helper functions for the project"""

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
