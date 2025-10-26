"""
This file makes the 'models' directory a Python package.
Models are dynamically imported by Alembic and other parts of the application
to prevent circular dependencies and SQLAlchemy metadata conflicts.
Do not add model imports here.
"""

from ..database import Base
