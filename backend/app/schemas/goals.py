from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, FutureDate

from app.utils.goal import StatusEnum


class GoalBase(BaseModel):
    name: str = Field(
        max_length=80,
        default="Goal Name",
        description="Name of the Goal you want to remember",
    )
    description: str = Field(
        default="Goal Description",
        description="Description of the Goal you want to remember",
    )
    status: StatusEnum = Field(StatusEnum.ACTIVE, description="User status")
    due_date: FutureDate = Field(description="Due date")


class GoalCreate(GoalBase): ...


class GoalUpdate(GoalBase): ...


class GoalRead(GoalBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    status: StatusEnum
    due_date: datetime

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
        json_encoders = {StatusEnum: lambda v: v.value}
