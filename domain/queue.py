import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.models import Task


def submit_task(db: Session, payload: dict, idempotency_key: str | None = None) -> Task:
    if idempotency_key:
        existing = db.execute(
            select(Task).where(Task.idempotency_key == idempotency_key)
        ).scalar_one_or_none()
        if existing:
            return existing  # idempotent: same key returns the same task, no duplicate

    task = Task(
        id=uuid.uuid4(),
        status="pending",
        payload=payload,
        idempotency_key=idempotency_key,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def claim_task(db: Session) -> Task | None:
    """
    Atomically claim the next available task.
    FOR UPDATE SKIP LOCKED lets multiple workers poll concurrently:
    each worker locks the row it's checking, and any other worker
    running this same query simply skips locked rows instead of
    blocking or double-claiming them.
    """
    stmt = (
        select(Task)
        .where(Task.status == "pending")
        .where(Task.run_after <= datetime.utcnow())
        .order_by(Task.run_after)
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    task = db.execute(stmt).scalar_one_or_none()
    if task is None:
        return None

    task.status = "claimed"
    task.claimed_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return task


def complete_task(db: Session, task: Task) -> Task:
    task.status = "done"
    db.commit()
    db.refresh(task)
    return task


def fail_task(db: Session, task: Task, backoff_seconds: int = 30) -> Task:
    """Retry with exponential backoff; permanently give up after max_attempts."""
    task.attempts += 1
    if task.attempts >= task.max_attempts:
        task.status = "dead_letter"
    else:
        task.status = "pending"
        task.run_after = datetime.utcnow() + timedelta(
            seconds=backoff_seconds * (2 ** (task.attempts - 1))
        )
        task.claimed_at = None
    db.commit()
    db.refresh(task)
    return task