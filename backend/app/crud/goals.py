from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional

from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status

from app.models.goals import Goal
from app.schemas.goals import GoalUpdate, GoalRead

# from app.models import Goal  # Ensure Goal is imported


async def read_all_goals(db: Session, user_id: int) -> list:
    """
    Retrieve all goals for a specific user.

    Args:
        db (Session): Database session
        user_id (int): ID of the user

    Returns:
        List of GoalRead objects
    """
    goals = db.query(Goal).filter(Goal.user_id == user_id).all()
    return goals


async def read_goal_by_id(goal_id: int, user_id: int, db: Session) -> dict:
    """
    Retrieve a specific goal by ID for a user.

    Args:
        goal_id (int): ID of the goal
        user_id (int): ID of the user
        db (Session): Database session

    Returns:
        Goal object or None if not found
    """
    goal = (
        db.query(Goal)
        .filter(Goal.id == goal_id, Goal.user_id == user_id)
        .first()
    )
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"goal with ID {goal_id} not found",
        )
    return goal


async def create_goal(goal: Goal, db: Session) -> GoalRead:
    """
    Create a new goal.

    Args:
        goal (Goal): Goal object to create
        db (Session): Database session

    Returns:
        Created GoalRead object
    """
    try:
        db.add(goal)
        db.commit()
        db.refresh(goal)
        return GoalRead
    except SQLAlchemyError as e:
        db.rollback()
        raise e


async def update_goal(
    goal_id: int, user_id: int, data: GoalUpdate, db: Session
) -> Optional[GoalRead]:
    """
    Update an existing goal.

    Args:
        goal_id (int): ID of the goal to update
        user_id (int): ID of the user
        data (GoalUpdate): Updated goal data
        db (Session): Database session

    Returns:
        Updated GoalRead object or None if not found
    """
    try:
        goal = (
            db.query(Goal)
            .filter(Goal.id == goal_id, Goal.user_id == user_id)
            .first()
        )

        if not goal:
            return None

        # Update only provided fields
        goal.name = data.name
        goal.description = data.description

        db.commit()
        db.refresh(goal)
        return goal

    except SQLAlchemyError:
        db.rollback()
        raise


async def delete_goal(goal_id: int, user_id: int, db: Session) -> bool:
    """
    Delete a goal.

    Args:
        goal_id (int): ID of the goal to delete
        user_id (int): ID of the user
        db (Session): Database session

    Returns:
        True if goal was deleted, False otherwise
    """
    try:
        goal = (
            db.query(Goal)
            .filter(Goal.id == goal_id, Goal.user_id == user_id)
            .first()
        )

        if not goal:
            return False

        db.delete(goal)
        db.commit()
        return True

    except SQLAlchemyError as e:
        db.rollback()
        raise e


async def get_goal_by_id(db: Session, goal_id: int):
    """
    Retrieve a specific goal by its ID with its related motivations.
    ...
    """
    try:
        # Query the database to find the goal by ID with joined motivations
        goal = (
            db.query(Goal)
            .options(
                joinedload(Goal.motivation)
            )  # Eager load the singular motivation
            .filter(Goal.id == goal_id)
            .first()
        )

        # If no goal is found, raise a 404 error
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Goal with ID {goal_id} not found",
            )

        return goal

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving the goal:{e}.",
        )


async def get_user_id_by_goal_id(goal_id: int, db):
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        return None
    return goal.user_id


# TODO: verify if the goal belongs to the user


async def get_goal_for_qr_generation(
    goal_id: int, user_id: int, db: Session
) -> Goal:
    """
    Retrieve a goal for QR code generation with strict ownership verification.

    Args:
        goal_id (int): ID of the goal to retrieve
        user_id (int): ID of the user attempting to access the goal
        db (Session): Database session

    Returns:
        Goal: The retrieved goal

    Raises:
        HTTPException: If goal is not found or user does not own the goal
    """
    try:
        # Fetch the goal with a direct filter on both goal and user_id
        goal = (
            db.query(Goal)
            .filter(Goal.id == goal_id, Goal.user_id == user_id)
            .first()
        )

        # Check if goal exists
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="goal not found or you do not have permission to access it",
            )

        return goal

    except SQLAlchemyError as e:
        # Log the error for debugging
        print(f"Database error in get_goal_for_qr_generation: {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the goal",
        )


async def validate_qr_access(goal_id: int, user_id: int, db: Session) -> Goal:
    """
    Validate QR code access for a specific goal.

    Args:
        goal_id (int): ID of the goal to validate
        user_id (int): ID of the user attempting to access the goal
        db (Session): Database session

    Returns:
        goal: The validated goal

    Raises:
        HTTPException: If access is not permitted
    """
    try:
        # Fetch the goal with a direct filter on both goal and user_id
        goal = (
            db.query(Goal)
            .filter(Goal.id == goal_id, Goal.user_id == user_id)
            .first()
        )

        # Check if goal exists
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this goal",
            )

        return goal

    except SQLAlchemyError as e:
        # Log the error for debugging
        print(f"Database error in validate_qr_access: {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while validating goal access",
        )


async def store_qr_access_log(
    goal: int, user_id: int, access_method: str, db: Session
):
    """
    Log QR code access attempts for security and auditing purposes.

    Args:
        goal (int): ID of the goal accessed
        user_id (int): ID of the user accessing the goal
        access_method (str): Method of access (e.g., 'qr_code', 'token')
        db (Session): Database session
    """
    try:
        # In a real-world scenario, you'd create an access log model
        # For now, we'll just print the access attempt
        print(
            f"QR Access Log: goal {goal} accessed by User {user_id} via {access_method}"
        )

        # If you have an AccessLog model, you would create a record here
        # access_log = AccessLog(
        #     goal=goal,
        #     user_id=user_id,
        #     access_method=access_method,
        #     timestamp=datetime.utcnow()
        # )
        # db.add(access_log)
        # db.commit()

    except Exception as e:
        # Log any errors in logging (ironic, but important)
        print(f"Error in store_qr_access_log: {str(e)}")
        # Optionally, you could add more robust error handling here
