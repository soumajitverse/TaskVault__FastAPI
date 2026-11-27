from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database.session import get_db
from app.models.user import User

# Standard HTTP Bearer scheme for Swagger UI Authorization (simple token paste dialog)
security = HTTPBearer()


def get_current_user(
    auth_header: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Dependency that extracts, decodes, and validates the JWT Bearer token,

    returning the authenticated User from the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = auth_header.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    try:
        user = db.scalar(select(User).where(User.id == int(user_id)))
    except (ValueError, TypeError):
        raise credentials_exception

    if user is None:
        raise credentials_exception

    return user


def require_role(required_role: str):
    """Reusable dependency factory for Role-Based Access Control (RBAC).

    Raises 403 Forbidden if the authenticated user's role does not match.
    """

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Requires {required_role} role.",
            )
        return current_user

    return role_checker


# Convenient pre-configured dependency for Admin endpoints
require_admin = require_role("ADMIN")