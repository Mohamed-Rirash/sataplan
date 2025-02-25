from datetime import timedelta, datetime, timezone
from typing import Any, Annotated, Dict, Optional
from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from app.config import ALGORITHM, SECRET_KEY
from app.models.users import User
from jose import JWTError, jwt, ExpiredSignatureError
from sqlalchemy.orm import Session
import logging
import urllib.parse

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


async def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password (str): The password to hash

    Returns:
        str: The hashed password
    """
    return pwd_context.hash(password)


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password (str): The plain password to verify
        hashed_password (str): The hashed password to compare against

    Returns:
        bool: True if the passwords match, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def decode_token(token: str) -> dict:
    """
    Decode and verify a JWT token with more detailed error handling.

    Args:
        token (str): JWT token to decode

    Returns:
        dict: Decoded token payload

    Raises:
        HTTPException: If token is invalid, expired, or cannot be decoded
    """
    try:
        # Decode the JWT token
        # Attempt to handle URL-encoded tokens

        token = urllib.parse.unquote(token)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        # Handle invalid tokens
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Invalid token: {str(e)}",
        )
    except ExpiredSignatureError as e:
        # Handling for tokens with invalid structure
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Invalid token structure: {str(e)}",
        )


# step 1: authenticate user
async def authenticate_user(username_or_email: str, password: str, db: Session):
    """
    Authenticate a user by username or email and password.

    Args:
        username_or_email (str): Username or email of the user
        password (str): Plain text password
        db (Session): Database session

    Returns:
        User or None: Authenticated user or None if authentication fails
    """

    # Check if the input is an email or username based on the presence of '@'
    if "@" in username_or_email:
        user = db.query(User).filter(User.email == username_or_email).first()

    else:
        user = db.query(User).filter(User.username == username_or_email).first()

    # If no user found, return None
    if not user:
        return None

    # Verify password
    try:
        is_password_correct = await verify_password(password, user.password)

    except Exception:
        return None

    return user if is_password_correct else None


# step 2: create access token
async def create_access_token(username: str, user_id: int, plan_id: int = None):
    """
    Create access and refresh tokens for an authenticated user.

    Args:
        username (str): Username of the authenticated user
        user_id (int): ID of the authenticated user
        plan_id (int, optional): ID of the plan associated with the token

    Returns:
        tuple: Access token and refresh token
    """
    access_token_expires = timedelta(minutes=15)
    refresh_token_expires = timedelta(days=7)

    try:
        # Create token payload with optional plan_id
        access_token_payload = {
            "sub": username,  # Use username as sub
            "id": user_id,  # Use id for user identification
            "exp": datetime.now(timezone.utc) + access_token_expires,
        }

        # Add plan_id to payload if provided
        if plan_id is not None:
            access_token_payload["plan_id"] = plan_id

        access_token = jwt.encode(
            access_token_payload,
            SECRET_KEY,
            algorithm=ALGORITHM,
        )

        # Similar modification for refresh token
        refresh_token_payload = {
            "sub": username,
            "id": user_id,
            "exp": datetime.now(timezone.utc) + refresh_token_expires,
        }

        refresh_token = jwt.encode(
            refresh_token_payload,
            SECRET_KEY,
            algorithm=ALGORITHM,
        )

        return access_token, refresh_token

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token generation error: {str(e)}",
        )


# step 3: get current user
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="could not validate user",
            )
        return {
            "username": username,
            "id": user_id,
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="could not validate user",
        )


async def create_access_token_for_qrcode(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = timedelta(minutes=15),
) -> str:
    """
    Create a JWT access token with flexible payload and expiration.

    Args:
        data (Dict[str, Any]): Payload data to be encoded in the token
        expires_delta (Optional[timedelta], optional): Token expiration time.
Defaults to 15 minutes.

    Returns:
        str: Encoded JWT token

    Raises:
        HTTPException: If token generation fails
    """
    try:
        # Validate input
        if not isinstance(data, dict):
            raise ValueError("Token payload must be a dictionary")

        # Create a copy of the payload to avoid modifying the original
        to_encode = data.copy()

        # Set expiration time with timezone awareness
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=15)
        )
        to_encode.update({"exp": expire})

        # Validate required fields (optional, but recommended)
        if "type" not in to_encode:
            logger.warning("Token generated without specifying token type")

        # Encode the token
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        # Log token generation (be careful not to log sensitive information)
        logger.info(
            f"Access token generated for type: {to_encode.get('type', 'unknown')}"
        )

        return encoded_jwt

    except ValueError as ve:
        logger.error(f"Invalid token payload: {str(ve)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid token payload: {str(ve)}",
        )

    except Exception as e:
        logger.error(f"Token generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate access token",
        )
