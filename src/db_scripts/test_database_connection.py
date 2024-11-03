"""Runs simple test to check if database connection is working
"""
# Import modules
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from src.constants import POSTGRESDB_CON_STRING
from src.logger_definition import get_logger

logger = get_logger(__file__)

# Create conection to scraping database defined in kubernetes
try:
    # Create an engine to establish a connection
    engine = create_engine(POSTGRESDB_CON_STRING)

    # Try to connect to the database
    connection = engine.connect()

    # Connection successful
    logger.info("Connected to the PostgreSQL database!")

    # Close the connection
    connection.close()

except OperationalError as error:
    # Connection failed
    logger.info("Failed to connect to the PostgreSQL database:", error)
