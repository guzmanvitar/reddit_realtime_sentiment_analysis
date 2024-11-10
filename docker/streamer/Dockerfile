FROM python:3.11.10

# Export env variables
ENV PROJECT reddit_realtime_sentiment_analysis
ENV HOME /home

# Install poetry
RUN pip install poetry>=1.0.0

# create a project directory inside project home
ENV PROJECT_DIR $HOME/$PROJECT
RUN mkdir $PROJECT_DIR

WORKDIR $PROJECT_DIR

# Copy poetry installation files
COPY poetry.lock $PROJECT_DIR/
COPY pyproject.toml $PROJECT_DIR/

# Copy python scripts
COPY ./src/streamer/reddit_streamer.py $PROJECT_DIR/src/streamer/reddit_streamer.py
COPY ./src/constants.py $PROJECT_DIR/src/constants.py
COPY ./src/logger_definition.py $PROJECT_DIR/src/logger_definition.py

# Add execute permissions
RUN chmod +x $PROJECT_DIR/src/streamer/reddit_streamer.py

# Install poetry dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# # expose port for jupyter lab
# EXPOSE 8787

# # define password for jupyter
# ENV JUPYTER_TOKEN eureka