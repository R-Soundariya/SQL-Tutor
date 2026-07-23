"""ORM models for SQL Interview Coach AI.

Empty for now. Domain tables (topics, questions, attempts, sessions, progress
stats, etc.) are introduced in the phases that need them, so each model lands
alongside the feature that uses it rather than as a speculative schema here.
"""

from app.core.db.engine import Base

__all__ = ["Base"]
