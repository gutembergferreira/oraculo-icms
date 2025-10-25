from datetime import datetime

from pydantic import EmailStr

from app.schemas.base import OraculoBaseModel


class UserBase(OraculoBaseModel):
    email: EmailStr
    first_name: str
    last_name: str


class UserCreate(UserBase):
    password: str
    organization_name: str | None = None


class UserRead(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TokenResponse(OraculoBaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
