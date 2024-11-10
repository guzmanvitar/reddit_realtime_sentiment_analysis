FROM bitnami/kafka:latest

# Install dependencies and kcat
USER root
RUN apt-get update && \
    apt-get install -y kafkacat

# Copy your health check script if needed
COPY ./scripts/kafka-healthcheck.sh /kafka-healthcheck.sh
RUN chmod +x /kafka-healthcheck.sh

# Set back to non-root user if necessary
USER 1001
