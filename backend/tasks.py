from collections import defaultdict
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class TaskStatus(Enum):
    NOT_FOUND = "not_found"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Task(BaseModel):
    id: str
    status: TaskStatus
    start_time: datetime | None
    result: dict | None
    error: str | None


class TaskStore:
    _instance = None
    _tasks = defaultdict(dict)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TaskStore, cls).__new__(cls)
        return cls._instance

    def set_task(self, task_id: str, task_data: Task):
        self._tasks[task_id] = task_data

    def get_task(self, task_id: str) -> Task:
        return self._tasks.get(task_id)


task_store = TaskStore()