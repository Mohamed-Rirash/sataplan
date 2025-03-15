from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from .config import DATABASE_URL


Base = declarative_base()


engine = create_engine(DATABASE_URL)

LocalSession = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)
