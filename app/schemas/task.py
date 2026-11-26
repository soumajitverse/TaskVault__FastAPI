from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

"""Field(...): The ... (called an Ellipsis in Python) means this field is strictly required. A client must provide a title.
min_length=1, max_length=100: Enforces that title cannot be an empty string "" and cannot exceed 100 characters (matching our String(100) in PostgreSQL).
description: str | None = None: This field is optional. If the client doesn't provide it, it defaults to None (SQL NULL).
status: str = Field(default="PENDING", max_length=20): If the client doesn't specify a status, it automatically defaults to "PENDING"."""
class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    status: str = Field(default="PENDING", max_length=20)

"""Inherits all fields directly from TaskBase.
When someone creates a task (POST /tasks), they only provide title, description, and optionally status.
Using pass keeps our code DRY (Don't Repeat Yourself)—we don't duplicate the fields!"""
class TaskCreate(TaskBase):
    pass

"""Notice it does NOT inherit from TaskBase. Why?
In an update operation, every single field should be optional. A user might only want to change the status from "PENDING" to "COMPLETED" without re-sending the title.
If we inherited from TaskBase, title would be strictly required on every update request."""
class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    status: str | None = Field(default=None, max_length=20)

"""Inherits title, description, and status from TaskBase.
Adds fields generated exclusively by the database/server:
id: The auto-incremented primary key.
owner_id: The ID of the user who owns this task.
created_at: The server timestamp.
The Secret Sauce: model_config = ConfigDict(from_attributes=True):
In normal Python, dictionaries access data via keys: data["title"].
SQLAlchemy queries return database ORM objects that access data via attributes: task.title, task.id.
By default, Pydantic throws an error if you pass it an ORM object instead of a dictionary.
from_attributes=True (formerly orm_mode = True in Pydantic v1) tells Pydantic: "It is okay if the input is a SQLAlchemy object; extract its values by reading attributes (task.id, task.title) and convert them into clean JSON."""
class TaskResponse(TaskBase):
    id: int
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)