from fastapi import Depends
from sqlalchemy.orm import Session
from typing import Annotated, Iterator

from app.db import LocalSession, engine
from app.models.users import Base
from app.services.security import get_current_user

# qrcode dependency
from fastapi import Depends, HTTPException, status
from app.services.security import decode_token
from app.crud.users import get_user_pass_by_id
from sqlalchemy.orm import Session


# Create all tables if they don't exist
Base.metadata.create_all(bind=engine)


def get_db() -> Iterator[Session]:
    """
    Dependency that creates a new database session for each request
    and closes it after the request is complete.
    """
    db = LocalSession()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


user_dependency = Annotated[dict, Depends(get_current_user)]


async def qr_token_dependency(token: str, db: Session = Depends(get_db)):
    """
    Dependency to authenticate a user using a QR verification token
    """
    try:
        # Decode the token
        payload = decode_token(token)

        # Validate token type
        if payload.get("type") != "qr_verification":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        # Extract user ID from token
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing user ID in token",
            )

        # Convert user_id to integer
        try:
            user_id = int(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format",
            )

        # Fetch the user from the database
        user = await get_user_pass_by_id(user_id, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Return user information
        return {
            "user_id": user_id,
            "username": user.username,
            "email": user.email,
        }

    except HTTPException as e:
        # Re-raise the HTTP exception
        raise e
    except Exception as e:
        # Catch any unexpected errors
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )


qr_token_dependency = Annotated[dict, Depends(qr_token_dependency)]


# scurity dependency
#


user_dependency = Annotated[dict, Depends(get_current_user)]
