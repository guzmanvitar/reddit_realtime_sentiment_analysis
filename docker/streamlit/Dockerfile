# Use the same base image as your existing setup
FROM python:3.11.10

# Export environment variables
ENV PROJECT streamlit_sentiment_analysis_app
ENV HOME /home

# Install Poetry
RUN pip install poetry>=1.0.0

# Set up project directory
ENV PROJECT_DIR $HOME/$PROJECT
RUN mkdir $PROJECT_DIR

WORKDIR $PROJECT_DIR

# Copy Poetry installation files
COPY poetry.lock $PROJECT_DIR/
COPY pyproject.toml $PROJECT_DIR/

# Copy Python scripts
COPY ./src/streamlit/sentiment_analysis_streamlit.py $PROJECT_DIR/src/streamlit/sentiment_analysis_streamlit.py
COPY ./src/constants.py $PROJECT_DIR/src/constants.py
COPY ./src/logger_definition.py $PROJECT_DIR/src/logger_definition.py

# Add execute permissions
RUN chmod +x $PROJECT_DIR/src/streamlit/sentiment_analysis_streamlit.py

# Install dependencies with Poetry
RUN poetry config virtualenvs.create false \
    && poetry install --without dev --without ml --no-interaction --no-ansi

# Expose Streamlit default port
EXPOSE 8501
