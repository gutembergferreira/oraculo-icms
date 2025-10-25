from datetime import datetime

from pydantic import BaseModel


class OraculoBaseModel(BaseModel):
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class TimestampSchema(OraculoBaseModel):
    created_at: datetime | None = None
    updated_at: datetime | None = None
