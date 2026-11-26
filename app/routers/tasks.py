from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["Tasks"])


# 1. Create Task (automatically assigned to current_user)
@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
)
def create_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_task = Task(
        title=task_in.title,
        description=task_in.description,
        status=task_in.status,
        owner_id=current_user.id,  # Tied to the authenticated user!
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


# 2. List Only the Current User's Tasks
@router.get(
    "",
    response_model=list[TaskResponse],
    summary="List all tasks owned by current user",
)
def get_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Task).where(Task.owner_id == current_user.id)
    return db.scalars(query).all()


# 3. Get Single Task (enforcing ownership)
@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get a task by ID (owner only)",
)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Task).where(
        Task.id == task_id, Task.owner_id == current_user.id
    )
    task = db.scalar(query)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return task


# 4. Update Task (enforcing ownership)
@router.put(
    "/{task_id}", response_model=TaskResponse, summary="Update a task"
)
def update_task(
    task_id: int,
    task_in: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Task).where(
        Task.id == task_id, Task.owner_id == current_user.id
    )
    task = db.scalar(query)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    # Partial update: only update fields the user actually sent
    update_data = task_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    db.commit()
    db.refresh(task)
    return task


# 5. Delete Task (enforcing ownership)
@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Task).where(
        Task.id == task_id, Task.owner_id == current_user.id
    )
    task = db.scalar(query)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    db.delete(task)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)