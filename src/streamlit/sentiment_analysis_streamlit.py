from json import loads
from time import sleep

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
from confluent_kafka import Consumer

import streamlit as st
from src.constants import PREDICTIONS_TOPIC


class SentimentDashboard:
    def __init__(self, kafka_servers: str, group_id: str, topic: str):
        """
        Initializes the SentimentDashboard with Kafka Consumer configurations.

        :param kafka_servers: Kafka bootstrap servers.
        :param group_id: Kafka consumer group ID.
        :param topic: Kafka topic to subscribe to for sentiment data.
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
            self.sentiment_counts["positive"][tag] = self.sentiment_counts["positive"].get(tag, 0) + 1
        else:
            self.sentiment_counts["negative"][tag] = self.sentiment_counts["negative"].get(tag, 0) + 1

    def get_data_frame(self) -> pd.DataFrame:
        """Prepares the DataFrame for sentiment counts by tag."""
        tags = list(set(self.sentiment_counts["positive"].keys()).union(self.sentiment_counts["negative"].keys()))
        data = {
            "Tag": tags,
            "Total Count": [
                self.sentiment_counts["positive"].get(tag, 0) + self.sentiment_counts["negative"].get(tag, 0)
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
        text_placeholder = st.empty()

        while True:
            self.consume_messages()
            df = self.get_data_frame()

            # Plot bars with proportional colors
            with chart_placeholder.container():
                fig, ax = plt.subplots(figsize=(8, 6))
                for i, row in df.iterrows():
                    positive = row["Positive Count"]
                    negative = row["Negative Count"]
                    total = positive + negative
                    if total > 0:
                        # Calculate the proportional width of positive and negative sections
                        ax.bar(
                            row["Tag"],
                            positive,
                            color="green",
                            label="Positive" if i == 0 else "",
                        )
                        ax.bar(
                            row["Tag"],
                            negative,
                            bottom=positive,
                            color="red",
                            label="Negative" if i == 0 else "",
                        )
                ax.set_ylabel("Count")
                ax.set_title("Sentiment Distribution by Tag")
                ax.legend()
                st.pyplot(fig)

            # Display total interactions
            total_interactions = df["Total Count"].sum()
            positive_interactions = df["Positive Count"].sum()
            negative_interactions = df["Negative Count"].sum()
            text_placeholder.write(
                f"**Total Interactions:** {total_interactions} | **Positive:** {positive_interactions} | **Negative:** {negative_interactions}"
            )

            sleep(5)  # Adjust the refresh rate as needed for performance


if __name__ == "__main__":
    dashboard = SentimentDashboard(
        kafka_servers="kafka:9092",
        group_id="streamlit-dashboard",
        topic=PREDICTIONS_TOPIC
    )

    # Configure Kafka Consumer
    dashboard.configure_consumer()

    # Run the dashboard
    dashboard.display_dashboard()
