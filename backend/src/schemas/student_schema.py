import uuid

from pydantic import BaseModel, Field
from typing import Optional

class StudentRead(BaseModel):
    student_id: uuid.UUID = Field(...)
    first_name: str = Field(...)
    last_name: str = Field(...)
    patronymic: Optional[str] = Field(...)
    group: str = Field(...)

    model_config = {"from_attributes": True}

class StudentCreate(BaseModel):
    first_name: str
    last_name: str
    patronymic: Optional[str] = None
    group: str