import datetime
import logging
import secrets
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse

from app.config import FRONTEND_URL
from app.crud.goals import (
    get_goal_by_id,
    get_user_id_by_goal_id,
)
from app.crud.users import (
    get_user_pass_by_id,
)
from app.dependencies import db_dependency, user_dependency
from app.services.qrcode import generate_qrcode
from app.services.security import (
    create_access_token_for_qrcode,
    decode_token,
    verify_password,
)

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Add global goal_PASSWORDS dictionary
goal_PASSWORDS: Dict[int, Dict[str, Any]] = {}


class AuthorizationError(HTTPException):
    """Custom exception for authorization-related errors."""

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=detail
        )


class ValidationError(HTTPException):
    """Custom exception for validation-related errors."""

    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def validate_user(user: Optional[dict]) -> int:
    """
    Validate user authentication and extract user ID.

    Args:
        user (Optional[dict]): User authentication data

    Returns:
        int: Validated user ID

    Raises:
        AuthorizationError: If user authentication fails
    """
    if not user or not isinstance(user, dict):
        logger.warning("Invalid user authentication")
        raise AuthorizationError(
            "User not authenticated or invalid authentication"
        )

    user_id = user.get("id") or user.get("user_id")
    if not user_id:
        logger.warning("Unable to determine user ID")
        raise AuthorizationError("Unable to determine user ID")

    return user_id


router = APIRouter(
    prefix="/qrcode",
    tags=["qrcode"],
)


@router.get("/generate-permanent-qr/{goal_id}")
async def generate_permanent_qrcode(
    user: user_dependency,db: db_dependency, goal_id: int
):
    """
    Generate a permanent QR code for a specific goal with a unique password.

    Args:
        user (user_dependency): Authenticated user
        goal_id (int): ID of the goal to generate QR code for
        db (db_dependency): Database session

    Returns:
        StreamingResponse: QR code image with goal password in header

    Raises:
        AuthorizationError: If user is not authenticated
        ValidationError: If goal does not belong to user
    """
    try:
        # Validate user and get user ID
        user_id = validate_user(user)
        logger.debug(f"User ID: {user_id}")

        # Verify the goal exists and belongs to the user
        goal = await get_goal_by_id(db, goal_id)
        logger.debug(f"Goal fetched: {goal}")  # Log the goal object

        # Ensure the goal belongs to the authenticated user
        if goal.user_id != user_id:
            logger.warning(
                f"Unauthorized QR code generation attempt. goal ID: {goal_id}, User ID: {user_id}"
            )
            raise AuthorizationError(
                "You do not have permission to generate QR for this goal"
            )

        # Generate a secure, random password for this goal
        goal_password = secrets.token_urlsafe(8)  # 8 characters of URL-safe random bytes

        # Store the goal password with additional context
        goal_PASSWORDS[goal_id] = {
            "password": goal_password,
            "user_id": user_id,
            "created_at": datetime.datetime.utcnow(),
        }

        # Construct the verification URL with goal_id
        verification_url = f"{FRONTEND_URL}/?goal_id={goal_id}"
        logger.info(f"Generated QR code for goal ID: {goal_id}")

        # Generate QR code with the verification URL
        qr_image = await generate_qrcode(data=verification_url)

        # Return the QR code image as a streaming response
        return StreamingResponse(
            qr_image,
            media_type="image/png",
            headers={
                "Content-Disposition": "attachment; filename=permanent_qrcode.png",
                "X-goal-Password": goal_password,  # Send password in a custom header
            },
        )

    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except AuthorizationError as e:
        logger.error(f"Authorization error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error generating QR code: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the QR code.",
        )


@router.post("/verify-goal-access")
async def verify_goal_access(goal_id: int, password: str, db: db_dependency):
    """
    Verify the goal-specific password and user ownership.

    Args:
        goal_id (int): ID of the goal to verify
        password (str): Password to verify
        db (db_dependency): Database session

    Returns:
        JSONResponse: Access token if verification is successful

    Raises:
        ValidationError: If the goal is not found
        AuthorizationError: If credentials are invalid
    """
    try:
        # Check if the goal exists
        goal = await get_goal_by_id(db, goal_id)
        logger.debug(f"Goal fetched: {goal}")  # Log the goal object

        if not goal:
            logger.warning(f"Attempt to access non-existent goal: {goal_id}")
            raise ValidationError("Goal not found")

        # Get user ID associated with the goal
        user_id = await get_user_id_by_goal_id(goal.id, db)
        logger.info(f"Verifying goal access. goal ID: {goal_id}, User ID: {user_id}")

        # Get user's hashed password
        hashed_password = await get_user_pass_by_id(user_id, db)

        # Verify password
        if not await verify_password(password, hashed_password):
            logger.warning(f"Invalid access attempt for goal ID: {goal_id}")
            raise AuthorizationError("Invalid access credentials")

        # Generate access token
        access_token = await create_access_token_for_qrcode(
            data={
                "goal_id": goal_id,
                "user_id": user_id,
                "type": "permanent_qr_access",

            },
            expires_delta=datetime.timedelta(minutes=15),  # Short-lived access
        )

        logger.info(f"Access token generated for goal ID: {goal_id}")

        return JSONResponse(status_code=200, content={"token": access_token})

    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except AuthorizationError as e:
        logger.error(f"Authorization error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error verifying goal access: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while verifying goal access.",
        )


@router.get("/view-goal")
async def view_goal(
    token: str,
    db: db_dependency,
):
    """
    View goal details using the access token.

    Args:
        token (str): Access token
        db (db_dependency): Database session

    Returns:
        JSONResponse: Goal details or error message

    Raises:
        AuthorizationError: If token is invalid
    """
    try:
        # Decode and verify the token
        payload = decode_token(token)

        # Validate token type
        allowed_types = ["permanent_qr_access", "qr_onetime"]
        if payload.get("type") not in allowed_types:
            logger.warning(f"Invalid token type: {payload.get('type')}")
            raise AuthorizationError("Invalid token")

        # Extract goal_id from the token
        goal_id = payload.get("goal_id")
        if not goal_id:
            logger.warning("Token missing goal_id")
            raise AuthorizationError("Invalid token")

        # Fetch the goal
        goal_details = await get_goal_by_id(db, goal_id)

        logger.info(f"Goal details retrieved. goal ID: {goal_id}")
        return JSONResponse(
            status_code=200,
            content={
                "goal_id": goal_details.id,
                "goal_details": {
                    "name": goal_details.name,
                    "description": goal_details.description,
                    "motivations": [
                        {
                            "id": motivation.id,
                            "quote": motivation.quote,
                            "link": motivation.link,
                        }
                        for motivation in goal_details.motivation
                    ],
                },
            },
        )

    except AuthorizationError as e:
        logger.warning(f"Access denied: {str(e)}")
        return JSONResponse(
            status_code=401,
            content={
                "error": "Access Denied",
                "message": str(e.detail),
                "code": "TOKEN_ERROR"
            },
        )

    except Exception as e:
        logger.error(f"Unexpected error viewing goal: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "An unexpected error occurred"},
        )
