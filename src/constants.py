"""Defines project wide constants"""

from pathlib import Path

# Path constants
this = Path(__file__)

ROOT = this.parents[1]

LOGS = ROOT / "logs"

DATA = ROOT / "data"

SECRETS = ROOT / ".secrets"

DATA_RAW = DATA / "raw"
DATA_POSTS = DATA_RAW / "posts"
DATA_COMMENTS = DATA_RAW / "comments"

DATA_READY = DATA / "ready"
DATA_INTERIM = DATA / "interim"

MODELS = ROOT / "models"

LOGS.mkdir(exist_ok=True, parents=True)
DATA_RAW.mkdir(exist_ok=True, parents=True)
DATA_READY.mkdir(exist_ok=True, parents=True)
DATA_INTERIM.mkdir(exist_ok=True, parents=True)


# Postgres connection, as defined by sqlalchemy formating, and by user, password and name defined in
# docker compose service.
POSTGRESDB_CON_STRING = "postgresql://admin:admin@scraping-database:5432/postgresdb"


# Columns
TABLE_ID = "table_id"
DATE = "date"
VALUE = "value"
FULL_RESPONSE = "full_response"
