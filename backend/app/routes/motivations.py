import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import load_only

from app.crud.goals import read_goal_by_id
from app.dependencies import db_dependency, user_dependency
from app.models import Goal, Motivation
from app.schemas.motivations import MotivationCreate

from uuid import UUID

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter(
    prefix="/motivations",
    tags=["motivations"],
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


def get_user_goal(db, goal_id: int, user_id: int):
    """
    Retrieve a Goal for a specific user.

    Args:
        db: Database session
        oalGoal_id (int): oalGoal ID
        user_id (int): User ID

    Returns:
        Goal: Retrieved Goal

    Raises:
        ValidationError: If Goal is not found
    """
    goal = db.query(Goal).filter(Goal.id == goal_id).first()

    if not goal:
        logger.warning(
            f"Goal not found for user. Goal ID: {goal_id}, User ID: {user_id}"
        )
        raise ValidationError(f"Goal with ID {goal_id} not found for this user")

    return goal


@router.post("/{goal_id}", status_code=status.HTTP_201_CREATED)
async def add_motivation(
    goal_id: UUID,
    db: db_dependency,
    user: user_dependency,
    data: MotivationCreate,
):
    """
    Create a new motivation for a specific Goal.
    ...
    """
    try:
        # Validate user and get user ID
        user_id = validate_user(user)

        # Validate motivation data
        # if not data.quote:
        #     raise ValidationError("Motivation quote is required")

        # Verify the Goal exists and belongs to the user
        goal = await read_goal_by_id(goal_id, user_id, db)

        # check if link is already exists for this goal
        a if data.link:
        #     if db.query(Motivation).filter(Motivation.link == str(data.link)).first():
        #         raise ValidationError("Motivation link already exists for this goal")
        # check if the exact qout exist for this goal
        if db.query(Motivation).filter(Motivation.quote == data.quote).first():
            raise ValidationError(
                "Motivation quote already exists for this goal"
            )

        # Create motivation
        motivation = Motivation(
            quote=data.quote,
            link=str(data.link) if data.link else None,
            goal_id=goal.id,
        )

        db.add(motivation)
        db.commit()
        db.refresh(motivation)

        logger.info(
            f"Motivation created successfully. ID: {motivation.id}, Goal ID: {goal_id}"  # Fixed here
        )
        return {
            "message": "Motivation created successfully",
            "motivation_id": motivation.id,
        }

    except (ValidationError, AuthorizationError) as e:
        raise e

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during motivation creation: {str(e)}")
        raise ValidationError(f"Database error: {str(e)}")

    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during motivation creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )


@router.get("/{goal_id}")
async def get_motivations_by_goal(
    goal_id: UUID, db: db_dependency, user: user_dependency
) -> dict:
    """
    Retrieve all motivations for a specific Goal.
    ...
    """
    try:
        # Validate user and get user ID
        user_id = validate_user(user)

        # Verify the Goal exists and belongs to the user
        goal = await read_goal_by_id(goal_id, user_id, db)  # Change here

        # Retrieve motivations for the Goal
        motivations = (
            db.query(Motivation)
            .options(
                load_only(
                    Motivation.id,
                    Motivation.link,
                    Motivation.quote,
                    Motivation.goal_id,
                )
            )
            .filter(Motivation.goal_id == goal.id)  # Change here
            .all()
        )

        # Construct the response
        response = [
            {
                "id": m.id,
                "link": m.link,
                "quote": m.quote,
                "Goal_id": goal.id,
            }  # Change here
            for m in motivations
        ]

        # Add a check for empty motivations
        if not response:
            logger.info(f"No motivations found for Goal ID: {goal.id}")
            return {"data": []}

        logger.info(
            f"Retrieved {len(response)} motivations for Goal ID: {goal.id}"
        )
        return {"data": response}

    except (ValidationError, AuthorizationError) as e:
        raise e

    except Exception as e:
        logger.error(f"Error retrieving motivations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving motivations",
        )


@router.delete("/{motivation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_motivation(
    motivation_id: UUID, db: db_dependency, user: user_dependency
):
    """
    Delete a specific motivation.

    Args:
        motivation_id (UUID): The ID of the motivation to delete
        db (db_dependency): Database session
        user (user_dependency): User authentication data

    Returns:
        Response: No content on success

    Raises:
        ValidationError: If motivation is not found or belongs to another user
        AuthorizationError: If user is not authenticated
        HTTPException: For unexpected server errors
    """
    try:
        # Validate user and get user ID
        user_id = validate_user(user)

        # Retrieve the motivation and ensure it belongs to the user
        motivation = (
            db.query(Motivation)
            .join(Goal)
            .filter(Motivation.id == motivation_id, Goal.user_id == user_id)
            .first()
        )

        if not motivation:
            logger.warning(
                f"Motivation deletion attempt failed. "
                f"Motivation ID: {motivation_id}, User ID: {user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Motivation with ID {motivation_id} not found or not authorized",
            )

        # Delete the motivation
        db.delete(motivation)

        try:
            db.commit()
            logger.info(f"Motivation deleted successfully. ID: {motivation_id}")
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        except SQLAlchemyError as db_error:
            db.rollback()
            logger.error(
                f"Database error during motivation deletion: {str(db_error)}. "
                f"Motivation ID: {motivation_id}, User ID: {user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred while deleting motivation",
            )

    except (ValidationError, AuthorizationError) as auth_error:
        raise auth_error

    except Exception as e:
        logger.error(f"Unexpected error during motivation deletion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during motivation deletion",
        )
