import logging
from datetime import datetime
from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError
from sqlalchemy import select, and_, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import selectinload, joinedload

from app.dependencies import db_dependency, user_dependency
from app.models import Goal, Motivation
from app.schemas.goals import GoalRead, GoalUpdate
from app.services.uploadimg import Uploader
from app.utils.goal import Status

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter(
    prefix="/goals",
    tags=["goals"],
)


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


KB = 1024
MB = 1024 * KB

SUPPORTED_IMAGE_FORMATS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


async def async_upload_image(cover_image: UploadFile) -> str:
    """
    Asynchronously upload image to storage with robust error handling.

    Args:
        cover_image (UploadFile): Image file to upload

    Returns:
        str: URL of the uploaded image
    """
    try:
        # Validate file presence
        if not cover_image:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No cover image provided"
            )

        # Validate file size and type using existing Uploader logic
        image_url = await Uploader(cover_image)

        return image_url

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/add", status_code=status.HTTP_201_CREATED)
async def create_goal(
    background_tasks: BackgroundTasks,
    db: db_dependency,
    user: user_dependency,
    name: Annotated[str, Form(...)],
    description: Annotated[str, Form(...)],
    status: Annotated[str, Form(...)],
    due_date: str = Form(None),
    cover_image: UploadFile = File(...)
) -> dict:
    """
    Create a new goal with optimized image upload and database handling.

    Args:
        background_tasks (BackgroundTasks): FastAPI background tasks
        db (db_dependency): Database session
        user (user_dependency): Authenticated user
        name (str): Goal name
        description (str): Goal description
        status (str): Goal status
        due_date (Optional[str]): Goal due date
        cover_image (UploadFile): Goal cover image

    Returns:
        dict: Goal creation response
    """
    try:
        # Validate user and get user ID
        user_id = validate_user(user)

        # Validate input data
        if len(name) > 80:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Goal name must be at most 80 characters long"
            )

        if not description:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Goal description is required"
            )

        if status not in Status.__members__:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid status value: {status}"
            )

        # Parse and validate due_date
        parsed_due_date = None
        if due_date:
            try:
                parsed_due_date = datetime.fromisoformat(due_date)
                if parsed_due_date < datetime.now():
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Due date must be in the future"
                    )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid due date format. Use YYYY-MM-DD"
                )

        # Upload image
        image_url = await async_upload_image(cover_image)

        # Create goal with efficient database operation
        goal = Goal(
            name=name,
            description=description,
            user_id=user_id,
            status=status,
            due_date=parsed_due_date,
            cover_image=image_url,
        )

        # Use a single transaction for goal creation
        try:
            db.add(goal)
            db.commit()
            db.refresh(goal)
        except IntegrityError as ie:
            db.rollback()
            logger.error(f"Database integrity error: {str(ie)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Goal creation failed due to data constraints"
            )

        logger.info(
            f"Goal created successfully. ID: {goal.id}, User ID: {user_id}"
        )
        return {"message": "Goal created successfully", "goal_id": goal.id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected goal creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during goal creation"
        )


@router.get("/allgoals", response_model=List[GoalRead])
async def get_all_goals(
    db: db_dependency,
    user: user_dependency,
    offset: int = 0,
    limit: int = 10,
    status: Optional[str] = None  # New optional filter
) -> List[GoalRead]:
    """
    Retrieve goals for the authenticated user with advanced filtering.

    Args:
        db (db_dependency): The database session.
        user (user_dependency): The authenticated user's information.
        offset (int, optional): Pagination offset. Defaults to 0.
        limit (int, optional): Number of goals to retrieve. Defaults to 10.
        status (str, optional): Filter goals by status.

    Returns:
        List[GoalRead]: A list of goals belonging to the user.

    Raises:
        AuthorizationError: If the user is not authenticated
    """
    try:
        # Validate user and get user ID
        user_id = validate_user(user)

        # Build flexible query with optional filtering
        query = select(Goal).where(Goal.user_id == user_id)

        # Add optional status filter
        if status and status in Status.__members__:
            query = query.where(Goal.status == status)

        # Apply ordering and pagination
        query = query.order_by(Goal.created_at.desc()).offset(offset).limit(limit)

        # Execute query efficiently
        result = db.scalars(query).all()

        # Log retrieval details
        logger.info(f"Retrieved {len(result)} goals for user ID: {user_id}")
        return list(result)

    except Exception as e:
        logger.error(f"Error retrieving goals: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving goals",
        )


@router.get("/goal/{goal_id}", response_model=GoalRead)
async def get_goal(
    goal_id: UUID,
    db: db_dependency,
    user: user_dependency
) -> GoalRead:
    """
    Retrieve a specific goal by its ID for the authenticated user.

    Args:
        goal_id (UUID): The ID of the goal to retrieve.
        db (db_dependency): The database session.
        user (user_dependency): The authenticated user's information.

    Returns:
        GoalRead: The requested goal.

    Raises:
        HTTPException: If goal is not found or user is unauthorized
    """
    try:
        # Validate user and get user ID
        user_id = validate_user(user)

        # Fetch the goal
        goal_query = select(Goal).where(
            and_(Goal.id == goal_id, Goal.user_id == user_id)
        )
        goal = db.scalar(goal_query)

        # Check if goal exists
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Goal not found"
            )

        logger.info(f"Retrieved goal: {goal_id} for user: {user_id}")
        return goal

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving goal: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving goal"
        )


@router.patch("/update/{goal_id}", response_model=GoalRead)
async def update_goal(
    goal_id: UUID,
    data: GoalUpdate,
    db: db_dependency,
    user: user_dependency
) -> GoalRead:
    """
    Update an existing goal for the authenticated user.

    Args:
        goal_id (UUID): The ID of the goal to update.
        data (GoalUpdate): The updated goal data.
        db (db_dependency): The database session.
        user (user_dependency): The authenticated user's information.

    Returns:
        GoalRead: The updated goal.

    Raises:
        HTTPException: For validation or authorization errors
    """
    try:
        # Validate user and get user ID
        user_id = validate_user(user)

        # Validate input data
        if not data.name or len(data.name) > 80:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Goal name is required and must be at most 80 characters"
            )

        if not data.description:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Goal description is required"
            )

        # Find the goal with a single, efficient query
        query = select(Goal).where(
            and_(Goal.id == goal_id, Goal.user_id == user_id)
        )
        goal = db.scalars(query).first()

        if not goal:
            logger.warning(
                f"Goal not found for update. Goal ID: {goal_id}, User ID: {user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Goal with ID {goal_id} not found"
            )

        # Validate status if provided
        if data.status and data.status not in Status.__members__:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid status: {data.status}"
            )

        # Update goal attributes
        goal.name = data.name
        goal.description = data.description
        goal.status = data.status or goal.status
        goal.due_date = data.due_date or goal.due_date

        # Commit changes
        db.commit()
        db.refresh(goal)

        logger.info(
            f"Goal updated successfully. Goal ID: {goal_id}, User ID: {user_id}"
        )
        return goal

    except HTTPException:
        raise
    except IntegrityError as ie:
        db.rollback()
        logger.error(f"Database integrity error: {str(ie)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid data provided"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during goal update: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.delete("/delete/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: UUID,
    db: db_dependency,
    user: user_dependency
):
    """
    Delete a goal for the authenticated user.

    Args:
        goal_id (UUID): The ID of the goal to delete.
        db (db_dependency): The database session.
        user (user_dependency): The authenticated user's information.

    Raises:
        HTTPException: For authorization or not found errors
    """
    try:
        # Validate user and get user ID
        user_id = validate_user(user)

        # Find the goal with a single, efficient query
        query = select(Goal).where(
            and_(Goal.id == goal_id, Goal.user_id == user_id)
        )
        goal = db.scalars(query).first()

        if not goal:
            logger.warning(
                f"Goal not found for deletion. Goal ID: {goal_id}, User ID: {user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Goal with ID {goal_id} not found"
            )

        # Delete the goal
        db.delete(goal)
        db.commit()

        logger.info(
            f"Goal deleted successfully. Goal ID: {goal_id}, User ID: {user_id}"
        )

    except HTTPException:
        raise
    except IntegrityError as ie:
        db.rollback()
        logger.error(f"Database integrity error during deletion: {str(ie)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete goal due to existing dependencies"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during goal deletion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )
