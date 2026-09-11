import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, JSON, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from core.db import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String, nullable=False, default="pending")  # pending, claimed, done, dead_letter
    payload = Column(JSON, nullable=False, default=dict)
    idempotency_key = Column(String, nullable=True, unique=True)
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=3)
    run_after = Column(DateTime, nullable=False, default=datetime.utcnow)
    claimed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_tasks_status_run_after", "status", "run_after"),
    )


class DeadLetter(Base):
    __tablename__ = "dead_letters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    payload = Column(JSON, nullable=False)
    failure_reason = Column(String, nullable=True)
    attempts_made = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)