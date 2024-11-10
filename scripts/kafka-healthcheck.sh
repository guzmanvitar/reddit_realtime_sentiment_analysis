#!/bin/bash
# kafka-healthcheck.sh

echo "Running Kafka health check on kafka:9092..."

# Check if Kafka is available by listing brokers with kafkacat
kcat -b kafka:9092 -L > /dev/null 2>&1

# Capture the exit status of kafkacat
if [ $? -eq 0 ]; then
    echo "Kafka is healthy."
    exit 0
else
    echo "Kafka is not healthy."
    exit 1
fi
