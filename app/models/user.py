from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.task import Task


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="USER", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # 1-to-many relationship: One User has many Tasks
    tasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="owner", cascade="all, delete-orphan"
    )

"""Python Object Level: relationship()
In raw SQL, to get a user and their tasks, you'd have to write JOIN queries manually every time. relationship() allows you to navigate between objects directly in Python:
Mapped[list["Task"]]: Tells Python that accessing user.tasks returns a list of Task objects.
  
back_populates="owner": Tells SQLAlchemy: "This matches the .owner attribute over on the Task model."
  
cascade="all, delete-orphan": If you delete a task from Python's user.tasks list (or delete the user object), SQLAlchemy automatically issues a DELETE SQL statement for that task."""