import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TaskSubmitRequest(BaseModel):
    payload: dict
    idempotency_key: Optional[str] = None


class TaskResponse(BaseModel):
    id: uuid.UUID
    status: str
    payload: dict
    attempts: int
    created_at: datetime

    class Config:
        from_attributes = True