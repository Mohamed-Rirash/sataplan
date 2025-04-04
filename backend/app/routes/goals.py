import logging
from datetime import datetime
from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.dependencies import db_dependency, user_dependency
from app.models import Goal
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


# @router.post("/add", status_code=status.HTTP_201_CREATED)
# async def create_goal(
#     data: GoalCreate,
#     db: db_dependency,
#     user: user_dependency,
#     cover_image: UploadFile = File(...),
# ) -> dict:
#     """
#     Create a new goal for the authenticated user.
#     ...
#     """
#     goal = None  # Initialize goal to None
#     try:
#         # Validate user and get user ID
#         user_id = validate_user(user)
#         content = await cover_image.read()

#         image_url = upload_image(image=content)

#         # Validate goal data
#         if not data.name or not data.description:
#             raise ValidationError("goal name and description are required")

#         # Create the goal
#         goal = Goal(
#             name=data.name,
#             description=data.description,
#             user_id=user_id,
#             status=data.status,
#             due_date=data.due_date,
#             cover_image=image_url,
#         )
#         db.add(goal)
#         db.commit()
#         db.refresh(goal)

#         logger.info(
#             f"goal created successfully. ID: {goal.id}, User ID: {user_id}"
#         )
#         return {"message": "goal created successfully", "goal_id": goal.id}

#     except (ValidationError, AuthorizationError) as e:
#         raise e

#     except SQLAlchemyError as e:
#         db.rollback()
#         logger.error(f"Database error during goal creation: {str(e)}")
#         raise ValidationError(f"Database error: {str(e)}")

#     except Exception as e:
#         db.rollback()
#         if goal is not None:
#             logger.error(f"Unexpected error during goal creation: {str(e)}")
#         else:
#             logger.error(
#                 "Unexpected error during goal creation: goal was not created"
#             )
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="An unexpected error occurred",
#         )


KB = 1024
MB = 1024 * KB

SUPPORTED_IMAGE_FORMATS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


@router.post("/add", status_code=status.HTTP_201_CREATED)
async def create_goal(
    db: db_dependency,
    user: user_dependency,
    name: Annotated[str, Form(...)],
    description: Annotated[str, Form(...)],
    status: Annotated[str, Form(...)],
    due_date: Annotated[
        Optional[str], Form(...)
    ],  # Receive as string and parse
    cover_image: UploadFile = File(...),
) -> dict:
    """
    Create a new goal for the authenticated user.
    """
    try:
        # Validate user and get user ID
        user_id = validate_user(user)

        image_url = await Uploader(
            cover_image
        )  # **Manually validate fields similar to Pydantic**
        if len(name) > 80:
            raise HTTPException(
                status_code=422,
                detail="Goal name must be at most 80 characters long.",
            )

        if not description:
            raise HTTPException(
                status_code=422, detail="Goal description is required."
            )

        if (
            status not in Status.__members__
        ):  # Validate `status` is a valid enum value
            raise HTTPException(
                status_code=422, detail=f"Invalid status value: {status}"
            )

        # Parse and validate `due_date`
        parsed_due_date = None
        if due_date:
            try:
                parsed_due_date = datetime.fromisoformat(due_date)
                if parsed_due_date < datetime.now():
                    raise HTTPException(
                        status_code=422,
                        detail="Due date must be in the future.",
                    )
            except ValueError:
                raise HTTPException(
                    status_code=422,
                    detail="Invalid due date format. Use YYYY-MM-DD.",
                )

        # Create the goal
        goal = Goal(
            name=name,
            description=description,
            user_id=user_id,
            status=status,
            due_date=parsed_due_date,
            cover_image=image_url,
        )
        db.add(goal)
        db.commit()
        db.refresh(goal)

        logger.info(
            f"Goal created successfully. ID: {goal.id}, User ID: {user_id}"
        )
        return {"message": "Goal created successfully", "goal_id": goal.id}

    except HTTPException as e:
        raise e  # Return validation errors

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during goal creation: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred.")

    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500, detail="An unexpected error occurred."
        )


@router.get("/allgoals", response_model=List[GoalRead])
async def get_all_goals(
    db: db_dependency, user: user_dependency, offset: int = 0, limit: int = 10
) -> List[GoalRead]:
    """
    Retrieve all goals for the authenticated user.

    Args:
        db (db_dependency): The database session.
        user (user_dependency): The authenticated user's information.

    Returns:
        List[GoalRead]: A list of goals belonging to the user.

    Raises:
        AuthorizationError: If the user is not authenticated
        ValidationError: If no goals are found
    """
    try:
        # Validate user and get user ID
        user_id = validate_user(user)

        # Retrieve all goals for the user
        result = (
            db.query(Goal)
            .filter(Goal.user_id == user_id)
            .order_by(Goal.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        # Check for empty result set
        if not result:
            logger.info(f"No goals found for user ID: {user_id}")
            return []

        logger.info(f"Retrieved {len(result)} goals for user ID: {user_id}")
        return list(result)

    except (ValidationError, AuthorizationError) as e:
        raise e

    except Exception as e:
        logger.error(f"Unexpected error retrieving goals: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving goals",
        )


@router.get("/goal/{goal_id}", response_model=GoalRead)
async def get_goal(
    goal_id: UUID, db: db_dependency, user: user_dependency
) -> GoalRead:
    """
    Retrieve a specific goal by its ID for the authenticated user.

    Args:
        goal_id (int): The ID of the goal to retrieve.
        db (db_dependency): The database session.
        user (user_dependency): The authenticated user's information.

    Returns:
        GoalRead: The requested goal.

    Raises:
        AuthorizationError: If the user is not authenticated
        ValidationError: If the goal is not found
    """
    try:
        # Validate user and get user ID
        user_id = validate_user(user)

        # Retrieve the specific goal for the user
        result = (
            db.query(Goal)
            .filter(Goal.id == goal_id, Goal.user_id == user_id)
            .first()
        )

        if not result:
            logger.warning(
                f"goal not found. goal ID: {goal_id}, User ID: {user_id}"
            )
            raise ValidationError(
                f"goal with ID {goal_id} not found for this user"
            )

        logger.info(f"Retrieved goal. goal ID: {goal_id}, User ID: {user_id}")
        return result

    except (ValidationError, AuthorizationError) as e:
        raise e

    except Exception as e:
        logger.error(f"Unexpected error retrieving goal: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving goal",
        )


@router.patch("/update/{goal_id}", response_model=GoalRead)
async def update_goal(
    goal_id: UUID, data: GoalUpdate, db: db_dependency, user: user_dependency
) -> GoalRead:
    """
    Update an existing goal for the authenticated user.

    Args:
        goal_id (int): The ID of the goal to update.
        data (GoalUpdate): The updated goal data.
        db (db_dependency): The database session.
        user (user_dependency): The authenticated user's information.

    Returns:
        GoalRead: The updated goal.

    Raises:
        AuthorizationError: If the user is not authenticated
        ValidationError: If the goal data is invalid or goal not found
    """
    try:
        # Validate user and get user ID
        user_id = validate_user(user)

        # Validate goal data
        if not data.name or not data.description:
            raise ValidationError("goal name and description are required")

        # Attempt to update the goal
        goal = (
            db.query(Goal)
            .filter(Goal.id == goal_id, Goal.user_id == user_id)
            .first()
        )

        if not goal:
            logger.warning(
                f"goal not found for update. goal ID: {goal_id}, User ID: {user_id}"
            )
            raise ValidationError(
                f"goal with ID {goal_id} not found for this user"
            )

        # Update goal attributes
        goal.name = data.name
        goal.description = data.description
        goal.status = data.status
        goal.due_date = data.due_date

        db.commit()
        db.refresh(goal)

        logger.info(
            f"goal updated successfully. goal ID: {goal_id}, User ID: {user_id}"
        )
        return goal

    except (ValidationError, AuthorizationError) as e:
        raise e

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during goal update: {str(e)}")
        raise ValidationError(f"Database error: {str(e)}")

    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during goal update: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )


@router.delete("/delete/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(goal_id: UUID, db: db_dependency, user: user_dependency):
    """
    Delete a goal for the authenticated user.

    Args:
        goal_id (UUID): The ID of the goal to delete.
        db (db_dependency): The database session.
        user (user_dependency): The authenticated user's information.

    Raises:
        AuthorizationError: If the user is not authenticated
        ValidationError: If the goal is not found
    """
    try:
        # Validate user and get user ID
        user_id = validate_user(user)

        # Check if goal exists and belongs to user
        goal = (
            db.query(Goal)
            .filter(Goal.id == goal_id, Goal.user_id == user_id)
            .first()
        )

        if not goal:
            logger.warning(
                f"goal not found for deletion. goal ID: {goal_id}, User ID: {user_id}"
            )
            raise ValidationError(
                f"goal with ID {goal_id} not found for this user"
            )

        # Delete the goal
        db.delete(goal)
        db.commit()

        logger.info(
            f"goal deleted successfully. goal ID: {goal_id}, User ID: {user_id}"
        )

    except (ValidationError, AuthorizationError) as e:
        raise e

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during goal deletion: {str(e)}")
        raise ValidationError(f"Database error: {str(e)}")

    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during goal deletion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )
