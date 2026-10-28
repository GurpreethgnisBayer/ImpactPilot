"""SQLAlchemy ORM models."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from impactpilot.persistence.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class InitiativeRow(Base):
    __tablename__ = "initiatives"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(512), default="")
    focus_area_code: Mapped[str] = mapped_column(String(16), default="UN", index=True)
    phase_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    maturity_tier: Mapped[str] = mapped_column(String(32), default="exploratory", index=True)
    impact_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    signoff: Mapped[str] = mapped_column(String(32), default="pending")
    document_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    created_by: Mapped[str] = mapped_column(String(128), default="local-user")
    updated_by: Mapped[str] = mapped_column(String(128), default="local-user")


class InitiativeVersionRow(Base):
    __tablename__ = "initiative_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    initiative_id: Mapped[str] = mapped_column(String(36), index=True)
    version: Mapped[int] = mapped_column(Integer)
    document_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    created_by: Mapped[str] = mapped_column(String(128), default="local-user")
    reason: Mapped[str] = mapped_column(String(512), default="")


class AuditEventRow(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    initiative_id: Mapped[str] = mapped_column(String(36), index=True)
    actor: Mapped[str] = mapped_column(String(128), default="local-user")
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    path: Mapped[str] = mapped_column(String(512))
    old_value: Mapped[str] = mapped_column(Text, default="")
    new_value: Mapped[str] = mapped_column(Text, default="")
