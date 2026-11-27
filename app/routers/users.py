from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.database.session import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserRoleUpdate

router = APIRouter(prefix="/users", tags=["Users (Admin Only)"])


# 1. List All Users (Admin Only)
@router.get(
    "",
    response_model=list[UserResponse],
    summary="List all users (Admin only)",
)
def get_all_users(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Admin-only endpoint: Retrieve all registered users in TaskVault."""
    return db.scalars(select(User)).all()


# 2. Promote / Change a User's Role (Admin Only)
@router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
    summary="Update a user's role (Admin only)",
)
def update_user_role(
    user_id: int,
    role_in: UserRoleUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Admin-only endpoint: Promote a standard USER to ADMIN or demote back to USER."""
    target_user = db.scalar(select(User).where(User.id == user_id))
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    target_user.role = role_in.role
    db.commit()
    db.refresh(target_user)
    return target_user



# 2. Promote / Change a User's Role (Admin Only)
@router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
    summary="Update a user's role (Admin only)",
)
def update_user_role(
    user_id: int,
    role_in: UserRoleUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Admin-only endpoint: Promote a standard USER to ADMIN or demote back to USER."""
    target_user = db.scalar(select(User).where(User.id == user_id))
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    target_user.role = role_in.role
    db.commit()
    db.refresh(target_user)
    return target_user