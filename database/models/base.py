"""SQLAlchemy Declarative Base for ORM models."""
from sqlalchemy.orm import DeclarativeMeta, declarative_base

# Declarative Base for all ORM entities
# All feature-specific entities should inherit from this base
Base: DeclarativeMeta = declarative_base()
