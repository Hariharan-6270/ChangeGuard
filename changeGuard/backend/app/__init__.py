"""ChangeGuard Backend Application Package."""

__version__ = "1.0.0"
__author__ = "ChangeGuard Team"

from app.config import settings
from app.models import init_db

__all__ = ["settings", "init_db"]