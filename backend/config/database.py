from sqlalchemy import create_engine

DATABASE_URL = (
    "postgresql+psycopg://dota:dota@postgres:5432/dota"
)

engine = create_engine(
    DATABASE_URL,
    echo=True
)