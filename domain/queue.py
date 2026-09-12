import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.models import Task, DeadLetter


def submit_task(
    db: Session,
    payload: dict,
    idempotency_key: str | None = None,
    submitted_by: str | None = None,
    submitter_ip: str | None = None,
) -> Task:
    if idempotency_key:
        existing = db.execute(
            select(Task).where(Task.idempotency_key == idempotency_key)
        ).scalar_one_or_none()
        if existing:
            return existing

    task = Task(
        id=uuid.uuid4(),
        status="pending",
        payload=payload,
        idempotency_key=idempotency_key,
        submitted_by=submitted_by,
        submitter_ip=submitter_ip,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def claim_task(db: Session) -> Task | None:
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


def fail_task(db: Session, task: Task, backoff_seconds: int = 30, reason: str | None = None) -> Task:
    task.attempts += 1
    if task.attempts >= task.max_attempts:
        task.status = "dead_letter"
        dead = DeadLetter(
            id=uuid.uuid4(),
            task_id=task.id,
            payload=task.payload,
            failure_reason=reason,
            attempts_made=task.attempts,
        )
        db.add(dead)
    else:
        task.status = "pending"
        task.run_after = datetime.utcnow() + timedelta(
            seconds=backoff_seconds * (2 ** (task.attempts - 1))
        )
        task.claimed_at = None
    db.commit()
    db.refresh(task)
    return task