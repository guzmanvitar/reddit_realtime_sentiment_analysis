from pyspark.sql.types import StringType, StructField, StructType, TimestampType

streamer_schema = StructType(
    [
        StructField("tag", StringType()),
        StructField("id", StringType()),
        StructField("created_utc", TimestampType()),  # Assuming timestamp format
        StructField("text", StringType()),
        StructField("sentiment_label", StringType()),
        StructField("sentiment_score", StringType()),
    ]
)
