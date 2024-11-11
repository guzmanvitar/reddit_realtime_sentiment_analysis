from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, from_json
from pyspark.sql.functions import sum as spark_sum
from pyspark.sql.functions import udf, when, window
from pyspark.sql.types import FloatType, StringType
from transformers import pipeline

from src.schemas import streamer_schema

spark = SparkSession.builder.appName("RedditKafkaSentimentStream").getOrCreate()

# Load a pre-trained sentiment analysis model from Hugging Face
sentiment_model = pipeline(
    "sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english"
)

# Define a function to perform sentiment analysis
def analyze_sentiment(text):
    result = sentiment_model(text)[0]
    return result["label"], result["score"]


get_sentiment_label = udf(lambda text: analyze_sentiment(text)[0], StringType())
get_sentiment_score = udf(lambda text: analyze_sentiment(text)[1], FloatType())

#  Set up Kafka stream
kafka_stream = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "localhost:9092")
    .option("subscribe", "trump")
    .option("startingOffsets", "latest")
    .option("kafka.security.protocol", "PLAINTEXT")  # Ensure PLAINTEXT protocol
    .load()
)

# Parse JSON and process each record
parsed_stream = (
    kafka_stream.selectExpr("CAST(value AS STRING) as json_string")
    .select(from_json(col("json_string"), streamer_schema).alias("data"))
    .select("data.*")
)

# Apply the sentiment analysis model and add results to the DataFrame
sentiment_stream = parsed_stream \
    .withColumn("sentiment_label", get_sentiment_label(col("text"))) \
    .withColumn("sentiment_score", get_sentiment_score(col("text")))


# Aggregate sentiment results in 2-minute windows
sentiment_aggregated = sentiment_stream \
    .withColumn("is_positive", when(col("sentiment_label") == "POSITIVE", 1).otherwise(0)) \
    .groupBy("tag", window("created_utc", "2 minutes")) \
    .agg(
        count("*").alias("total_count"),
        spark_sum("is_positive").alias("positive_count"),
        (spark_sum("is_positive") / count("*")).alias("positive_percentage")
    )

# Convert to JSON and publish to Kafka
sentiment_output = sentiment_aggregated \
    .select(to_json(struct("*")).alias("value"))  # Serialize as JSON

query = sentiment_output.writeStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("topic", "sentiment_analysis_results") \
    .option("checkpointLocation", "/path/to/checkpoint") \
    .start()

query.awaitAnyTermination(timeout=300)
