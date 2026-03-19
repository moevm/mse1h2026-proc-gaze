import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class RecordingStatus(Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class RecordingRead(BaseModel):
    recording_id: uuid.UUID = Field(...)
    student_id: uuid.UUID = Field(...)
    created_at: datetime = Field(...)
    path_webcam: str = Field(...)
    path_screen: str = Field(...)
    status: RecordingStatus = Field(...)
    suspicion_level: float = Field(...)

    class Config:
        from_attributes = True
