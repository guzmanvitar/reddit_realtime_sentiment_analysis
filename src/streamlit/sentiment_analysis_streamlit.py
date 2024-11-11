from json import loads
from time import sleep

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
from confluent_kafka import Consumer

import streamlit as st
from src.constants import PREDICTIONS_TOPIC


class SentimentDashboard:
    """
    A real-time Streamlit dashboard for displaying sentiment analysis results from Reddit posts.
    This dashboard consumes sentiment data from a Kafka topic, processes it, and visualizes it
    in a bar chart with proportional color coding for positive and negative sentiments.

    Attributes:
    ----------
    kafka_servers : str
        The Kafka bootstrap servers.
    group_id : str
        The Kafka consumer group ID for the dashboard.
    topic : str
        The Kafka topic from which to consume sentiment predictions.
    consumer : confluent_kafka.Consumer
        The Kafka consumer instance used to retrieve messages.
    sentiment_counts : dict
        A dictionary to store and update the count of positive and negative interactions by tag.

    Methods:
    -------
    configure_consumer():
        Configures the Kafka consumer for the specified topic.
    consume_messages():
        Consumes messages from Kafka, updating sentiment counts for each tag.
    get_data_frame() -> pd.DataFrame:
        Returns a DataFrame with the total, positive, and negative sentiment counts by tag.
    display_dashboard():
        Displays the real-time dashboard with a plot of sentiment distribution and a summary table
        of total, positive, and negative interactions by tag.
    """

    def __init__(self, kafka_servers: str, group_id: str, topic: str):
        """
        Initializes the SentimentDashboard with Kafka Consumer configurations.

        Args:
            kafka_servers (str): Kafka bootstrap servers.
            group_id (str): Kafka consumer group ID.
            topic (str): Kafka topic to subscribe to for sentiment data.
        """
        self.kafka_servers = kafka_servers
        self.group_id = group_id
        self.topic = topic
        self.consumer = None
        self.sentiment_counts = {"positive": {}, "negative": {}}

    def configure_consumer(self):
        """Configures the Kafka consumer."""
        consumer_config = {
            "bootstrap.servers": self.kafka_servers,
            "group.id": self.group_id,
            "auto.offset.reset": "earliest",
        }
        self.consumer = Consumer(consumer_config)
        self.consumer.subscribe([self.topic])

    def consume_messages(self):
        """Consumes messages from Kafka and updates sentiment counts."""
        msg = self.consumer.poll(1.0)
        if msg is None:
            return
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            return

        message = loads(msg.value().decode("utf-8"))
        tag = message["tag"]
        sentiment_label = message["sentiment_label"]

        # Update counts
        if sentiment_label == "POSITIVE":
            self.sentiment_counts["positive"][tag] = (
                self.sentiment_counts["positive"].get(tag, 0) + 1
            )
        else:
            self.sentiment_counts["negative"][tag] = (
                self.sentiment_counts["negative"].get(tag, 0) + 1
            )

    def get_data_frame(self) -> pd.DataFrame:
        """Prepares the DataFrame for sentiment counts by tag."""
        tags = list(
            set(self.sentiment_counts["positive"].keys()).union(
                self.sentiment_counts["negative"].keys()
            )
        )
        data = {
            "Tag": tags,
            "Total Count": [
                self.sentiment_counts["positive"].get(tag, 0)
                + self.sentiment_counts["negative"].get(tag, 0)
                for tag in tags
            ],
            "Positive Count": [self.sentiment_counts["positive"].get(tag, 0) for tag in tags],
            "Negative Count": [self.sentiment_counts["negative"].get(tag, 0) for tag in tags],
        }
        return pd.DataFrame(data)

    def display_dashboard(self):
        """Displays the Streamlit dashboard with sentiment data."""
        st.title("Real-time Sentiment Analysis Dashboard")
        st.subheader("Sentiment Analysis on Reddit Tags")

        # Streamlit containers for dynamic content
        chart_placeholder = st.empty()
        table_placeholder = st.empty()
        text_placeholder = st.empty()

        while True:
            self.consume_messages()
            df = self.get_data_frame()

            # Plot bars with proportional colors
            with chart_placeholder.container():
                fig, ax = plt.subplots(figsize=(10, 6))
                for i, row in df.iterrows():
                    positive = row["Positive Count"]
                    negative = row["Negative Count"]
                    total = positive + negative
                    if total > 0:
                        # Check if the legend exists and only add label if it's not there
                        legend_texts = (
                            [legend.get_text() for legend in ax.get_legend().get_texts()]
                            if ax.get_legend()
                            else []
                        )
                        ax.bar(
                            row["Tag"],
                            positive,
                            color="green",
                            label="Positive" if "Positive" not in legend_texts else None,
                            width=0.6,
                        )
                        ax.bar(
                            row["Tag"],
                            negative,
                            bottom=positive,
                            color="red",
                            label="Negative" if "Negative" not in legend_texts else None,
                            width=0.6,
                        )

                # Beautify plot
                ax.set_title("Sentiment Distribution by Tag", fontsize=16, fontweight="bold")
                ax.set_ylabel("Count", fontsize=14)
                ax.set_xlabel("Tags", fontsize=14)
                ax.legend(loc="upper right", fontsize=12)
                ax.grid(axis="y", linestyle="--", alpha=0.7)

                # Customize y-axis ticks to integers
                ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))

                # Show the updated plot in Streamlit
                st.pyplot(fig)

            # Display total interactions by tag in a table format
            with table_placeholder.container():
                st.subheader("Total, Positive, and Negative Interactions by Tag")
                st.table(df[["Tag", "Total Count", "Positive Count", "Negative Count"]])

            # Display total interactions summary
            total_interactions = df["Total Count"].sum()
            positive_interactions = df["Positive Count"].sum()
            negative_interactions = df["Negative Count"].sum()
            text_placeholder.write(
                f"**Total Interactions:** {total_interactions}"
                f" | **Positive:** {positive_interactions}"
                f" | **Negative:** {negative_interactions}"
            )

            sleep(5)  # Adjust the refresh rate as needed for performance


if __name__ == "__main__":
    dashboard = SentimentDashboard(
        kafka_servers="kafka:9092", group_id="streamlit-dashboard", topic=PREDICTIONS_TOPIC
    )

    # Configure Kafka Consumer
    dashboard.configure_consumer()

    # Run the dashboard
    dashboard.display_dashboard()
