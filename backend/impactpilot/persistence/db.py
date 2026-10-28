"""SQLAlchemy engine and session helpers."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def _default_db_url() -> str:
    env = os.environ.get("IMPACTPILOT_DB_URL")
    if env:
        return env
    data_dir = Path(__file__).resolve().parents[3] / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{data_dir / 'impactpilot.db'}"


_ENGINE = None
_SessionLocal = None


def get_engine(url: str | None = None):
    global _ENGINE, _SessionLocal
    if _ENGINE is None or url is not None:
        db_url = url or _default_db_url()
        connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
        _ENGINE = create_engine(db_url, future=True, connect_args=connect_args)
        _SessionLocal = sessionmaker(bind=_ENGINE, autoflush=False, autocommit=False, future=True)
    return _ENGINE


def get_session_factory():
    get_engine()
    assert _SessionLocal is not None
    return _SessionLocal


def init_db(url: str | None = None) -> None:
    from impactpilot.persistence import models as _models  # noqa: F401

    engine = get_engine(url)
    Base.metadata.create_all(engine)


def session_scope() -> Generator[Session, None, None]:
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
