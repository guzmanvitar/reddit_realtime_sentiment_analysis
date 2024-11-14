#!/bin/bash

# Define variables for GCP repository base and service names
REPO_BASE="southamerica-east1-docker.pkg.dev/reddit-sentiment-stream-441421/reddit-sentiment-stream"
SERVICES=("python-poetry-env" "kafka" "reddit-streamer" "spark-kafka-sentiment" "streamlit-sentiment-dashboard")
TAG="latest"

# Loop through each service, build and push the Docker image
for SERVICE_NAME in "${SERVICES[@]}"; do
  IMAGE_NAME="$REPO_BASE/$SERVICE_NAME"
  DOCKERFILE_PATH="docker/$SERVICE_NAME/Dockerfile"

  echo "Building Docker image for $SERVICE_NAME..."
  docker build -t "$IMAGE_NAME:$TAG" -f "$DOCKERFILE_PATH" .

  # Check if the build was successful
  if [ $? -eq 0 ]; then
    echo "Docker build for $SERVICE_NAME successful. Pushing image to GCP..."
    docker push "$IMAGE_NAME:$TAG"

    # Check if the push was successful
    if [ $? -eq 0 ]; then
      echo "Docker image for $SERVICE_NAME pushed successfully!"
    else
      echo "Failed to push the Docker image for $SERVICE_NAME."
      exit 1
    fi
  else
    echo "Docker build for $SERVICE_NAME failed."
    exit 1
  fi
done

echo "All images built and pushed successfully!"
