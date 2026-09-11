from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from core.db import get_db
from domain.models import Task
from domain.queue import submit_task
from api.schemas import TaskSubmitRequest, TaskResponse

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse)
def create_task(req: TaskSubmitRequest, db: Session = Depends(get_db)):
    task = submit_task(db, payload=req.payload, idempotency_key=req.idempotency_key)
    return task


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    task = db.execute(select(Task).where(Task.id == task_id)).scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task