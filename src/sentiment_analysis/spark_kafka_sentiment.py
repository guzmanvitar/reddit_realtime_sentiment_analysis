import argparse

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, from_json, struct, to_json, udf
from pyspark.sql.types import FloatType, StringType
from transformers import pipeline

from src.constants import PREDICTIONS_TOPIC, STREAMER_TAGS
from src.schemas import streamer_schema
from src.utils import create_kafka_topic


class KafkaSentimentStream:
    """
    Class to set up a Kafka stream, process data, and apply sentiment analysis.
    """

    def __init__(self, kafka_bootstrap_servers: str, topic: str) -> None:
        """
        Initializes KafkaSentimentStream with Spark session and Kafka configurations.

        :param kafka_bootstrap_servers: Kafka server address.
        :param topic: Kafka topic for output.
        """
        self.spark = SparkSession.builder.appName("RedditKafkaSentimentStream").getOrCreate()
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.topic = topic
        self._initialize_udfs()

    def _initialize_udfs(self) -> None:
        """
        Registers UDFs for Spark to use the sentiment analyzer.
        """

        def analyze_sentiment(text: str) -> tuple[str, float]:
            """
            Analyzes the sentiment of the given text.
            Initializes the model on the worker node when the UDF is called.

            :param text: The input text to analyze.
            :return: A tuple containing the sentiment label and score.
            """
            sentiment_model = pipeline(
                "sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english"
            )
            result = sentiment_model(text)[0]
            return result["label"], result["score"]

        # Register the UDFs with Spark
        self.get_sentiment_label = udf(lambda text: analyze_sentiment(text)[0], StringType())
        self.get_sentiment_score = udf(lambda text: analyze_sentiment(text)[1], FloatType())

    def read_kafka_stream(self) -> DataFrame:
        """
        Reads the Kafka stream and parses the JSON content.

        :return: A Spark DataFrame representing the parsed Kafka stream.
        """
        kafka_stream = (
            self.spark.readStream.format("kafka")
            .option("kafka.bootstrap.servers", self.kafka_bootstrap_servers)
            .option("subscribe", ",".join(STREAMER_TAGS))
            .option("startingOffsets", "earliest")
            .option("kafka.security.protocol", "PLAINTEXT")
            .load()
        )

        parsed_stream = (
            kafka_stream.selectExpr("CAST(value AS STRING) as json_string")
            .select(from_json(col("json_string"), streamer_schema).alias("data"))
            .select("data.*")
        )

        return parsed_stream

    def apply_sentiment_analysis(self, stream: DataFrame) -> DataFrame:
        """
        Applies sentiment analysis to the parsed stream.

        :param stream: Parsed DataFrame from the Kafka stream.
        :return: DataFrame with sentiment analysis results.
        """
        return stream.withColumn(
            "sentiment_label", self.get_sentiment_label(col("text"))
        ).withColumn("sentiment_score", self.get_sentiment_score(col("text")))

    def write_to_kafka(self, stream: DataFrame) -> None:
        """
        Writes the sentiment analysis results to a specified Kafka topic.

        :param stream: DataFrame with sentiment analysis results to publish.
        """
        create_kafka_topic(self.topic)
        sentiment_output = stream.select(
            to_json(struct("tag", "text", "sentiment_label", "sentiment_score")).alias("value")
        )

        query = (
            sentiment_output.writeStream.format("kafka")
            .outputMode("append")
            .option("kafka.bootstrap.servers", self.kafka_bootstrap_servers)
            .option("topic", self.topic)
            .option("checkpointLocation", "/tmp/checkpoint")
            .start()
        )

        query.awaitTermination(timeout=300)

    def process_stream(self) -> None:
        """
        Main method to read Kafka stream, apply sentiment analysis, and write results back to Kafka.
        """
        parsed_stream = self.read_kafka_stream()
        sentiment_stream = self.apply_sentiment_analysis(parsed_stream)
        self.write_to_kafka(sentiment_stream)


def main() -> None:
    """
    Main function to parse arguments and start the Kafka sentiment stream processing.
    """
    parser = argparse.ArgumentParser(description="Kafka Sentiment Stream Processor")
    parser.add_argument(
        "--kafka_bootstrap_servers",
        type=str,
        default="kafka:9092",
        help="Kafka bootstrap servers",
    )
    parser.add_argument(
        "--output_topic",
        type=str,
        default=PREDICTIONS_TOPIC,
        help="Output Kafka topic for sentiment predictions",
    )

    args = parser.parse_args()

    # Instantiate and process the Kafka sentiment stream
    kafka_stream_processor = KafkaSentimentStream(
        kafka_bootstrap_servers=args.kafka_bootstrap_servers,
        topic=args.output_topic,
    )
    kafka_stream_processor.process_stream()


if __name__ == "__main__":
    main()
