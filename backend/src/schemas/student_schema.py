import uuid

from pydantic import BaseModel


class StudentRead(BaseModel):
    student_id: uuid.UUID