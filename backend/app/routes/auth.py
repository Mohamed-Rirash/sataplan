import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from sqlalchemy.exc import IntegrityError

from app.config import SECRET_KEY, ALGORITHM
from app.dependencies import db_dependency, user_dependency
from app.models.users import Profile, User
from app.schemas.users import (
    ProfileCreate,
    ProfileRead,
    ProfileUpdate,
    TokenResponse,
    UserCreate,
    UserRead,
)
from app.services.security import (
    authenticate_user,
    create_access_token,
    hash_password,
)

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthenticationError(HTTPException):
    """Custom exception for authentication-related errors."""

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=detail
        )


class UserValidationError(HTTPException):
    """Custom exception for user validation errors."""

    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: db_dependency) -> dict:
    """
    Create a new user account with comprehensive error handling.

    Args:
        user (UserCreate): User registration details
        db (db_dependency): Database session

    Returns:
        dict: Created user details

    Raises:
        HTTPException:
            - 400 if username or email already exists
            - 422 for validation errors
            - 500 for unexpected server errors
    """
    try:
        # Check if username or email already exists before creating
        existing_user_by_username = (
            db.query(User).filter(User.username == user.username).first()
        )
        existing_user_by_email = (
            db.query(User).filter(User.email == user.email).first()
        )

        if existing_user_by_username:
            logger.warning(
                f"Signup attempt with existing username: {user.username}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

        if existing_user_by_email:
            logger.warning(f"Signup attempt with existing email: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists",
            )

        # Hash the password before storing
        hashed_password = await hash_password(user.password)

        # Create new user
        created_user = User(
            username=user.username,
            email=user.email,
            password=hashed_password,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            # Consider email verification in future
        )

        db.add(created_user)

        try:
            db.commit()
            logger.info(f"User created successfully: {user.username}")
        except IntegrityError:
            db.rollback()
            logger.error(
                f"Database integrity error during user creation: {user.username}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already exists",
            )

        # Refresh to get the full user object with ID
        db.refresh(created_user)

        return {"message": "User created successfully"}

    except HTTPException:
        # Re-raise HTTPException to maintain original error handling
        raise

    except Exception as e:
        logger.error(f"Unexpected error during signup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during signup",
        ) from e


@router.post("/token", response_model=TokenResponse)
async def login(
    db: db_dependency, form_data: OAuth2PasswordRequestForm = Depends()
) -> TokenResponse:
    """
    Authenticate user and generate access tokens.

    Args:
        db (db_dependency): Database session
        form_data (OAuth2PasswordRequestForm): Login credentials

    Returns:
        TokenResponse: Access and refresh tokens

    Raises:
        AuthenticationError: For invalid credentials or inactive account
    """
    try:
        logger.info(f"Login attempt for: {form_data.username}")

        # Authenticate user
        user = await authenticate_user(
            username_or_email=form_data.username,
            password=form_data.password,
            db=db,
        )

        if not user:
            logger.warning(f"Failed login attempt: {form_data.username}")
            raise AuthenticationError("Invalid credentials")

        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {user.username}")
            raise AuthenticationError("Account is not active")

        # Generate tokens
        access_token, refresh_token = await create_access_token(
            username=user.username, user_id=user.id
        )

        logger.info(f"Successful login for user: {user.username}")
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=24 * 60 * 60,
        )

    except AuthenticationError as auth_error:
        raise auth_error
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during login",
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, db: db_dependency) -> TokenResponse:
    """
    Refresh access token using a valid refresh token.

    Args:
        refresh_token (str): Current refresh token
        db (db_dependency): Database session

    Returns:
        TokenResponse: New access and refresh tokens

    Raises:
        AuthenticationError: For invalid or expired tokens
    """
    try:
        # Decode and validate refresh token
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])

        username = payload.get("sub")
        user_id = payload.get("id")

        if not username or not user_id:
            logger.warning("Invalid refresh token payload")
            raise AuthenticationError("Invalid refresh token")

        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"Refresh token for non-existent user ID: {user_id}")
            raise AuthenticationError("User not found")

        # Generate new tokens
        new_access_token, new_refresh_token = await create_access_token(
            username=username, user_id=user_id
        )

        logger.info(f"Token refreshed for user: {username}")
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            access_token_expires_in=24 * 60 * 7,
            refresh_token_expires_in=24 * 60 * 15,  # it
        )

    except jwt.ExpiredSignatureError:
        logger.warning("Expired refresh token")
        raise AuthenticationError(
            "Refresh token has expired. Please log in again."
        )

    except (jwt.JWTError, AuthenticationError) as token_error:
        logger.error(f"Token validation error: {str(token_error)}")
        raise AuthenticationError("Invalid refresh token")

    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during token refresh",
        )


# -----------------------------------------------------------------------------------------------------
# user routes
guest_router = APIRouter(prefix="/user", tags=["user"])


# create user profile route
@guest_router.post(
    "/create-profile",
    status_code=status.HTTP_201_CREATED,
    response_model=ProfileRead,
)
async def create_user_profile(
    user: user_dependency, db: db_dependency, profile: ProfileCreate
):
    try:
        if not user:
            logger.error("User not authenticated")
            raise AuthenticationError("User not authenticated")

        user_id = user.get("id")
        logger.debug(f"User ID: {user_id}")

        # Check if user_id is None
        if user_id is None:
            logger.error("User ID is None. Cannot create profile.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID is required",
            )

        # Add validation for profile parameter
        if profile is None:
            logger.error("Profile data is missing")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Profile data is required",
            )

        # Check if this user has a profile already exists
        existing_profile = db.query(Profile).filter(Profile.user_id == user_id).first()
        if existing_profile:
            logger.error("User already has a profile")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has a profile",
            )

        new_profile = Profile(
            user_id=user_id,
            firstname=profile.firstname,
            lastname=profile.lastname,
            bio=profile.bio,
        )

        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)

        return new_profile
    except UserValidationError as ve:
        logger.error(f"Validation error: {str(ve)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ve.errors(),
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )


from sqlalchemy.orm import joinedload


@guest_router.get("/me", response_model=UserRead)
async def get_user(user: user_dependency, db: db_dependency) -> UserRead:
    try:
        if not user:
            logger.error("User not authenticated")
            raise AuthenticationError("User not authenticated")

        user_id = user.get("id")
        logger.debug(f"Attempting to retrieve user with ID: {user_id}")

        # Fetch the user along with their associated profile
        result = (
            db.query(User)
            .options(joinedload(User.profile))  # Eagerly load the profile
            .filter(User.id == user_id)
            .first()
        )

        if not result:
            logger.warning(f"User not found. User ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        logger.info(f"Retrieved user. User ID: {user_id}")

        # Convert the result to a dictionary to include profile information
        return UserRead(
            id=result.id,
            first_name=result.profile.firstname if result.profile else None,
            last_name=result.profile.lastname if result.profile else None,
            email=result.email,
            username=result.username,
            bio=result.profile.bio if result.profile else None,
            created_at=result.created_at.isoformat(),  # Convert to string for JSON serialization
        )
    except HTTPException as http_error:
        logger.error(f"HTTP error: {str(http_error)}")
        raise http_error
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )


@guest_router.put("/update-profile", response_model=ProfileRead)
async def update_user_profile(
    user: user_dependency, db: db_dependency, profile_update: ProfileUpdate
):
    try:
        if not user:
            logger.error("User not authenticated")
            raise AuthenticationError("User not authenticated")

        user_id = user.get("id")
        logger.debug(f"User ID: {user_id}")

        # Fetch the user's profile
        profile = db.query(Profile).filter(Profile.user_id == user_id).first()

        if not profile:
            logger.warning(f"Profile not found for User ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )

        # Update profile fields
        if profile_update.firstname is not None:
            profile.firstname = profile_update.firstname
        if profile_update.lastname is not None:
            profile.lastname = profile_update.lastname
        if profile_update.bio is not None:
            profile.bio = profile_update.bio

        # Commit the changes to the database
        db.commit()
        db.refresh(profile)  # Refresh to get updated data

        logger.info(f"Profile updated for User ID: {user_id}")
        return ProfileRead(
            id=profile.id,
            firstname=profile.firstname,
            lastname=profile.lastname,
            bio=profile.bio,
            user_id=profile.user_id,
        )
    except UserValidationError as ve:
        logger.error(f"Validation error: {str(ve)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ve.errors(),
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )
