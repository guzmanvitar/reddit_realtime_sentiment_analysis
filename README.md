# Reddit Real Time Sentiment Analysis on Reddit

This project demonstrates the integration of real-time streaming tools with machine learning inference, delivering live sentiment analysis on Reddit data. By combining Kafka, Spark, and Streamlit with a machine learning model, this pipeline showcases a scalable and flexible approach to processing and visualizing streaming data in real time.

## Project Overview
The goal is to build a comprehensive streaming pipeline that ingests Reddit posts and comments, analyzes their sentiment, and visualizes trends in real time. This project could be extended to monitor public opinion on any topic, making it a flexible tool for real time insights.

## How It Works
1. **Data Ingestion from Reddit**:

A custom Python script streams data from Reddit, filtering posts and comments based on a configurable list of tags. For each tag, a Kafka topic is created to structure the data flow.

2. **Sentiment Analysis with a Pre-trained Language Model:**

A Spark job listens to the Kafka topics, pulls in new posts, and applies a pre-trained language model to analyze sentiment. Sentiment predictions are then published to a separate Kafka topic.

3. **Real-Time Visualization:**

The final component of the pipeline, a Streamlit dashboard, listens to the prediction topics, aggregates the sentiment data, and visualizes trends in real-time, providing immediate insights on the chosen tags.

## Repo Setup

1. **Poetry**

This repo uses `poetry` to install and manage dependencies. We also use `pyenv` (see [here](https://github.com/pyenv/pyenv-installer)) to manage python versions.

The codebase uses `Python 3.11.10`. So after installing `pyenv` and `poetry` run
```bash
pyenv install 3.11.10
pyenv shell 3.11.10
pyenv which python | xargs poetry env use
poetry config virtualenvs.in-project true
poetry install
```
This will create a virtual environment and install all dependencies. Then, activate the `poetry` environment with:
```bash
    poetry shell
```
Once inside the shell, also run:
```bash
    pre-commit install
```
to set up Git hooks for code quality checks.

2. **Docker & Kubernetes**

We'll use GCP's kubernetes cluster for production, however, to locally test the kubernetes deployment you can install
`minikube` (see [here](https://minikube.sigs.k8s.io/docs/start/)).

Custom images in the Kubernetes YAML files are stored in a GCP Container Registry,
and Reddit credentials are retrieved from GCP secrets

 To run the code, you’ll need a `gcp_service_account_creds.json` file, which should be saved in
 the .secrets directory. Please contact me for this file.

If you're savy with Docker and GCP, you can build the images from the Dockerfiles,
push them to your own GCP registry, and update the Kubernetes YAML files as needed.

To log in to Docker with the credentials, use:
```bash
    cat .secrets/gcp_service_account_creds.json | docker login -u _json_key --password-stdin https://southamerica-east1-docker.pkg.dev
```

In Kubernetes, create secrets for Docker and the GCP service account with:
```bash
kubectl create secret docker-registry gcr-json-key \
--docker-server=southamerica-east1-docker.pkg.dev \
--docker-username=_json_key \
--docker-password="$(cat .secrets/gcp_service_account_creds.json)" \
--docker-email=any@valid.email
```
And also:
```bash
kubectl create secret generic gcp-service-account \
--from-file=gcp-credentials.json=.secrets/gcp_service_account_creds.json
```

You can verify the setup by running the Python environment container in Kubernetes:
```bash
    kubectl apply -f kubernetes/python-env.yaml
```

The python-env containers are built with the latest poetry.lock file in this repo, so you can execute the same commands locally or
within the development container. To access the container, either use kubectl exec or open Jupyter Lab at:
```bash
minikube service python-env --url
```

If you can access Jupyter Lab, the environment is correctly set up.

## Running the code
1. **Local run using docker-compose**

Before testing in any kind of prod worthy environment you can do a fast local test using docker-compose.

Just install [docker-compose](https://docs.docker.com/compose/install/), then run docker-compose up.

You should be able to access the streamlit sentiment analysis api in your browser on http://localhost:8501

2. **Local run using minikube kubernetes cluster**

Before deploying to a cloud-based Kubernetes cluster, you can test the deployment on your local machine using Minikube.
Note that the inference job is memory-intensive, so you’ll need to allocate sufficient resources when starting Minikube:
```bash
minikube start --memory=31845 --cpus=8
```
After Minikube is ready, deploy the Kubernetes configurations with:

```bash
kubectl apply -f kubernetes/
```
Once the pods are running, access the Streamlit app with:
```bash
kubectl port-forward <streamlit-sentiment-dashboard-pod> 8501:8501
```
This should open the Streamlit dashboard on http://localhost:8501.
