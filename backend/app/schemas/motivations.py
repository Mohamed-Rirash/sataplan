from pydantic import BaseModel, Field, HttpUrl
from typing import Optional


# class MotivationCreate(BaseModel):
#     """
#     Schema for creating a new motivation.
#     """

#     quote: Optional[str] = Field(
#         None,
#         min_length=0,
#         max_length=500,
#         description="Motivational quote text",
#     )
#     link: Optional[HttpUrl] = Field(
#         None, description="URL pointing to any media or social media"
#     )


from pydantic import model_validator


class MotivationCreate(BaseModel):
    """
    Schema for creating a new motivation.
    """

    quote: Optional[str] = Field(
        None,
        min_length=0,
        max_length=500,
        description="Motivational quote text",
    )
    link: Optional[HttpUrl] = Field(
        None, description="URL pointing to any media or social media"
    )

    @model_validator(mode="before")
    def check_at_least_one_field(cls, values):
        quote = values.get("quote")
        link = values.get("link")

        if quote is None and link is None:
            raise ValueError(
                "At least one of 'quote' or 'link' must be provided"
            )
        return values


class MotivationRead(BaseModel):
    id: int
    quote: str
    link: Optional[str]
    goal_id: int

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
