import uuid

from pydantic import BaseModel, Field


class StudentRead(BaseModel):
    student_id: uuid.UUID = Field(...)
    first_name: str = Field(...)
    last_name: str = Field(...)
    patronymic: str = Field(...)
    group: str = Field(...)