from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, struct, to_json, udf
from pyspark.sql.types import FloatType, StringType
from transformers import pipeline

from src.constants import STREAMER_TAGS
from src.schemas import streamer_schema
from src.utils import create_kafka_topic

# Initialize Spark session
spark = SparkSession.builder.appName("RedditKafkaSentimentStream").getOrCreate()

# Load a pre-trained sentiment analysis model from Hugging Face
sentiment_model = pipeline(
    "sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english"
)

# Define a function to perform sentiment analysis
def analyze_sentiment(text):
    result = sentiment_model(text)[0]
    return result["label"], result["score"]

# UDFs for sentiment analysis
get_sentiment_label = udf(lambda text: analyze_sentiment(text)[0], StringType())
get_sentiment_score = udf(lambda text: analyze_sentiment(text)[1], FloatType())

# Set up Kafka stream
kafka_stream = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", "kafka:9092")
    .option("subscribe", ",".join(STREAMER_TAGS))
    .option("startingOffsets", "earliest")
    .option("kafka.security.protocol", "PLAINTEXT")
    .load()
)

# Parse JSON and process each record
parsed_stream = (
    kafka_stream.selectExpr("CAST(value AS STRING) as json_string")
    .select(from_json(col("json_string"), streamer_schema).alias("data"))
    .select("data.*")
)

# Apply the sentiment analysis model and add results to the DataFrame
sentiment_stream = parsed_stream.withColumn(
    "sentiment_label", get_sentiment_label(col("text"))
).withColumn("sentiment_score", get_sentiment_score(col("text")))

# Create Kafka topic for results
create_kafka_topic("sentiment_predictions")

# Convert to JSON and publish to Kafka
sentiment_output = sentiment_stream.select(
    to_json(struct("tag", "text", "sentiment_label", "sentiment_score")).alias("value")
)

query = (
    sentiment_output.writeStream.format("kafka")
    .outputMode("append")
    .option("kafka.bootstrap.servers", "kafka:9092")
    .option("topic", "sentiment_predictions")
    .option("checkpointLocation", "/tmp/checkpoint")
    .start()
)

query.awaitTermination(timeout=300)
