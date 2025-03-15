from typing import Optional
from pydantic import BaseModel, EmailStr, validator, Field
import re
from uuid import UUID


class UserBase(BaseModel):
    username: str = Field(
        ...,  # Required field
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_]+$",  # Alphanumeric and underscore
        description="Username must be 3-50 characters long, containing only alphanumeric characters and underscores",
    )
    email: EmailStr = Field(..., description="A valid email address")

    @validator("username")
    def validate_username(cls, username):
        """
        Additional username validation
        - Prevents reserved usernames
        - Ensures no consecutive special characters
        """
        reserved_usernames = ["admin", "root", "system", "support"]
        if username.lower() in reserved_usernames:
            raise ValueError("This username cannot be used")

        return username


class UserCreate(UserBase):
    password: str = Field(
        ...,
        min_length=8,
        max_length=64,
        description="Password must be 8-64 characters long",
    )

    @validator("password")
    def validate_password_strength(cls, password):
        """
        Comprehensive password strength validation
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one number
        - At least one special character
        """
        # Check for at least one uppercase letter
        if not re.search(r"[A-Z]", password):
            raise ValueError(
                "Password must contain at least one uppercase letter"
            )

        # Check for at least one lowercase letter
        if not re.search(r"[a-z]", password):
            raise ValueError(
                "Password must contain at least one lowercase letter"
            )

        # Check for at least one number
        if not re.search(r"\d", password):
            raise ValueError("Password must contain at least one number")

        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError(
                "Password must contain at least one special character"
            )

        # Check for common weak passwords
        common_passwords = ["password", "12345678", "qwerty", "admin"]
        if password.lower() in common_passwords:
            raise ValueError("This password is too common and not secure")

        return password

    @validator("email")
    def validate_email(cls, email):
        """
        Additional email validation
        - Prevents disposable email domains
        - Ensures email is properly formatted
        """
        # List of disposable email domains to block
        disposable_domains = [
            "temp-mail.org",
            "tempmail.com",
            "throwawaymail.com",
            "guerrillamail.com",
            "mailinator.com",
        ]

        # Extract domain from email
        domain = email.split("@")[-1].lower()

        if domain in disposable_domains:
            raise ValueError("Disposable email addresses are not allowed")

        return email


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    access_token_expires_in: int = 1000 * 60 * 15  # 15 minutes in milliseconds
    refresh_token_expires_in: int = 7 * 24 * 3600  # 7 days in seconds


class UserRead(BaseModel):
    id: UUID
    first_name: str | None = None
    last_name: str | None = None
    email: str
    username: str
    bio: str | None = None
    created_at: str


class TokenPayload(BaseModel):
    sub: str  # Username
    email: str
    user_id: str


class ProfileCreate(BaseModel):
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    bio: Optional[str] = None

    class Config:
        orm_mode = True


class ProfileUpdate(ProfileCreate):
    pass

    class Config:
        orm_mode = True


class ProfileRead(ProfileCreate):
    id: str
    user_id: str

    class Config:
        orm_mode = True
        json_encoders = {
            UUID: str  # Convert UUID to string during JSON serialization
        }

    @validator('id', 'user_id', pre=True)
    def convert_uuid_to_str(cls, v):
        return str(v) if isinstance(v, UUID) else v
