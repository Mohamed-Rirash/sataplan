from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from .config import DATABASE_URL


Base = declarative_base()


engine = create_engine(
    DATABASE_URL,
    pool_size=10,  # Max number of connections in pool
    max_overflow=5,  # Extra connections when pool is full
    pool_timeout=30,  # Wait time for a connection before raising an error
    pool_recycle=1800,
)

LocalSession = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)
