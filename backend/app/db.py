from sqlalchemy.orm import scoped_session, sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from functools import lru_cache
import time
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

Base = declarative_base()


@lru_cache(maxsize=1)
def get_engine(database_url):
    """
    Lazily create and cache database engine with performance logging.

    Args:
        database_url (str): Database connection URL

    Returns:
        sqlalchemy.engine.base.Engine: Configured database engine
    """
    start_time = time.time()
    engine = create_engine(
        database_url,
        pool_size=10,  # Max number of connections in pool
        max_overflow=5,  # Extra connections when pool is full
        pool_timeout=30,  # Wait time for a connection before raising an error
        pool_recycle=1800,
    )
    logger.info(
        f"Database engine creation took {time.time() - start_time:.2f} seconds"
    )
    return engine


def get_session_factory(engine):
    """
    Create a session factory for the given engine.

    Args:
        engine (sqlalchemy.engine.base.Engine): Database engine

    Returns:
        sqlalchemy.orm.session.sessionmaker: Session factory
    """
    return scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=engine)
    )


class DatabaseSessionManager:
    """
    Manages database sessions with context manager support.
    """

    _engine = None
    _SessionLocal = None

    @classmethod
    def initialize(cls, database_url):
        """
        Initialize the database session manager.

        Args:
            database_url (str): Database connection URL
        """
        cls._engine = get_engine(database_url)
        cls._SessionLocal = get_session_factory(cls._engine)

    @classmethod
    def get_session(cls) -> Session:
        """
        Get a new database session.

        Returns:
            sqlalchemy.orm.Session: A new database session
        """
        if cls._SessionLocal is None:
            from .config import DATABASE_URL

            cls.initialize(DATABASE_URL)
        return cls._SessionLocal()

    @classmethod
    @contextmanager
    def session_scope(cls):
        """
        Provide a transactional scope around a series of operations.

        Yields:
            sqlalchemy.orm.Session: A database session
        """
        session = cls.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def get_db():
    """
    Dependency injection function for database sessions.

    Yields:
        sqlalchemy.orm.Session: A database session
    """
    db = DatabaseSessionManager.get_session()
    try:
        yield db
    finally:
        db.close()
