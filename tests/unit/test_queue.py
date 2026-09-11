import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.db import Base
from domain.queue import submit_task, claim_task, complete_task, fail_task


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_submit_task_creates_pending_task(db_session):
    task = submit_task(db_session, payload={"job": "test"})
    assert task.status == "pending"
    assert task.payload == {"job": "test"}


def test_submit_task_idempotency_key_returns_same_task(db_session):
    first = submit_task(db_session, payload={"job": "a"}, idempotency_key="key-1")
    second = submit_task(db_session, payload={"job": "b"}, idempotency_key="key-1")
    assert first.id == second.id


def test_claim_task_marks_it_claimed(db_session):
    submit_task(db_session, payload={"job": "test"})
    claimed = claim_task(db_session)
    assert claimed is not None
    assert claimed.status == "claimed"
    assert claimed.claimed_at is not None


def test_claim_task_returns_none_when_empty(db_session):
    result = claim_task(db_session)
    assert result is None


def test_complete_task_marks_it_done(db_session):
    submit_task(db_session, payload={"job": "test"})
    task = claim_task(db_session)
    done = complete_task(db_session, task)
    assert done.status == "done"


def test_fail_task_retries_with_backoff(db_session):
    submit_task(db_session, payload={"job": "test"})
    task = claim_task(db_session)
    retried = fail_task(db_session, task, backoff_seconds=10)
    assert retried.status == "pending"
    assert retried.attempts == 1
    assert retried.run_after > datetime.utcnow()


def test_fail_task_dead_letters_after_max_attempts(db_session):
    submit_task(db_session, payload={"job": "test"})
    task = claim_task(db_session)
    task.max_attempts = 1
    dead = fail_task(db_session, task)
    assert dead.status == "dead_letter"