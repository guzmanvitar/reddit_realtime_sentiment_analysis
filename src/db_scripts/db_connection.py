"""Defines docker postgres database conection and querying utilities.

"""

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.constants import POSTGRESDB_CON_STRING
from src.db_scripts import db_mappings


class PostgresDb:
    """Class containing database conection and querying functionality.

    Note that the query string imported from constants follows docker formating rules and uses
    name, user and password as defined in docker compose db service.
    """

    def __init__(self, constring: str = POSTGRESDB_CON_STRING):
        self._constring = constring
        self._create_engine(constring)
        self._create_table()
        self._define_session()

    def _create_engine(self, constring: str):
        """Initializes sqlalchemy connection based on a sqlalchemy connection string.

        More info at: https://docs.sqlalchemy.org/en/20/core/engines.html

        Args:
            constring (str): sqlalchemy connection string.
        """
        self.engine = create_engine(constring)

    def _create_table(self):
        """Initializes all tables defined in db_mappings on the database conected to self.engine."""
        db_mappings.Base.metadata.create_all(self.engine)

    def _define_session(self):
        """Starts a sqlalchemy session needed for table operations.

        More on sqlalchemy sessions: https://docs.sqlalchemy.org/en/14/orm/session.html
        """
        self.Session = sessionmaker(bind=self.engine)

    def execute_query(self, query_str: str) -> pd.DataFrame:
        """Queries the database and returns a pandas dataframe

        Args:
            query_str (str): sql query in string format

        Returns:
            pd.DataFrame: output dataframe
        """
        return pd.read_sql(query_str, con=self.engine)
