from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship back to User
    owner: Mapped["User"] = relationship("User", back_populates="tasks")

"""Database Level: ForeignKey (in Task)
In PostgreSQL, this creates an actual column in the tasks table named owner_id (an integer).
It tells PostgreSQL: "A task cannot exist unless its owner_id matches an existing id in the users table."
ondelete="CASCADE": If you delete a user in Postgres, Postgres itself immediately deletes all of their tasks.

Mapped["User"]: Tells Python that accessing task.owner returns a single User object (not a list).
  
back_populates="tasks": Points right back to user.tasks.
"""