FROM python:3.11.10

# Export env variables
ENV PROJECT=python_env
ENV HOME=/home

# Install java
RUN apt-get update && apt-get install -y openjdk-17-jre-headless

# Install poetry
RUN pip install poetry>=1.0.0

# create a project directory inside project home
ENV PROJECT_DIR=$HOME/$PROJECT
RUN mkdir $PROJECT_DIR

WORKDIR $PROJECT_DIR

# Copy poetry installation files
COPY poetry.lock $PROJECT_DIR/
COPY pyproject.toml $PROJECT_DIR/

# Copy python scripts
COPY ./src $PROJECT_DIR/src

# Create spark checkpoint folder
RUN mkdir -p /tmp/checkpoint && chmod -R 777 /tmp/checkpoint

# Add execute permissions
RUN chmod +x $PROJECT_DIR/src/*

# Install poetry dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Set JAVA_HOME for Spark compatibility
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:${PATH}"

# Expose port for jupyter
EXPOSE 8787

# Define password for jupyter
ENV JUPYTER_TOKEN eureka