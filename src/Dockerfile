FROM python:3.12.3

# Export env variables
ENV PROJECT x_realtime_sentiment_analysis
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

# Copy project and notebook files
COPY ./src/ $PROJECT_DIR/src
RUN mkdir $PROJECT_DIR/logs

# Add execute permissions to bash scripts
RUN chmod +x $PROJECT_DIR/src/bash/*

# Install poetry dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# expose port for jupyter lab
EXPOSE 8787

# define password for jupyter
ENV JUPYTER_TOKEN eureka