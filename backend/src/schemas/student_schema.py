import uuid

from pydantic import BaseModel, Field


class StudentRead(BaseModel):
    student_id: uuid.UUID = Field(...)
    first_name: str = Field(...)
    last_name: str = Field(...)
    patronymic: str = Field(...)
    group: str = Field(...)

    model_config = {"from_attributes": True}

class StudentCreate(BaseModel):
    first_name: str
    last_name: str
    patronymic: str
    group: str