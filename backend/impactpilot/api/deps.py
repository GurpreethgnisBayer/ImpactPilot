"""FastAPI dependencies."""

from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy.orm import Session

from impactpilot.persistence.db import get_session_factory
from impactpilot.persistence.repository import InitiativeRepository


def get_db() -> Generator[Session, None, None]:
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_repo(db: Session) -> InitiativeRepository:
    return InitiativeRepository(db)


def acting_as() -> str:
    return os.environ.get("IMPACTPILOT_ACTING_AS", "local-user")
