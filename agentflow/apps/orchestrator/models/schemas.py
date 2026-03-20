from pydantic import BaseModel
from enum import Enum
from typing import Optional


class RunStatus(str, Enum):
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class RunRequest(BaseModel):
    task_id: str
    task_description: str


class RunResponse(BaseModel):
    run_id: str
    status: RunStatus
    critic_score: Optional[float] = None
    final_output: Optional[str] = None
    revision_count: Optional[int] = None
