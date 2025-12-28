"""SQLAlchemy Base-Klasse und Datenbank-Konfiguration."""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, DeclarativeMeta

# Deklarative Basisklasse für alle Entities (SQLAlchemy 2.0 kompatibel)
Base: DeclarativeMeta = declarative_base()


def create_session_factory(database_url: str) -> sessionmaker:
    """
    Erstellt eine Session Factory für die Datenbank.

    Args:
        database_url: Verbindungs-URL zur Datenbank

    Returns:
        sessionmaker für die Datenbank
    """
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)
