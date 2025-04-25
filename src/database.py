from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager

# Database configuration
DB_FILE = 'database.sqlite'
DB_URL = f'sqlite:///{DB_FILE}'

# Create SQLite database engine
engine = create_engine(DB_URL, echo=False)

# Create session factory
Session = sessionmaker(bind=engine)

# Create base class for declarative models
Base = declarative_base()

def needs_initialization():
    """Check if database needs to be initialized by verifying table existence"""
    inspector = inspect(engine)
    required_tables = {'email_messages', 'email_threads', 'smart_folders'}
    existing_tables = set(inspector.get_table_names())
    return not required_tables.issubset(existing_tables)

def init_db():
    """Initialize the database schema if needed"""
    if needs_initialization():
        Base.metadata.create_all(engine)
        return True
    return False

@contextmanager
def get_session():
    """Context manager for database sessions"""
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
