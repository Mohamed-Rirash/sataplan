from pydantic import BaseModel, Field


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


class GoalCreate(GoalBase):
    pass


class GoalUpdate(GoalBase):
    pass


class GoalRead(GoalBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
