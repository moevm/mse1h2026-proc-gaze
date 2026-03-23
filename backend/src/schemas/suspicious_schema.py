import uuid
from datetime import time as time_type
from typing import List, Optional

from pydantic import BaseModel, Field


class SuspiciousRead(BaseModel):
    sus_id: uuid.UUID = Field(...)
    recording_id: uuid.UUID = Field(...)
    time: time_type = Field(...)
    duration: int = Field(...)
    description: str = Field(...)

    class Config:
        from_attributes = True
        json_encoders = {
            uuid.UUID: str,
            time_type: lambda v: v.isoformat() if v else None
        }



class SuspiciousInterval(BaseModel):
    time: time_type = Field(...)
    duration: int = Field(...)
    description: str = Field(...)

    class Config:
        from_attributes = True
        json_encoders = {
            time_type: lambda v: v.isoformat() if v else None
        }

class SuspiciousResult(BaseModel):
    recording_id: uuid.UUID = Field(...)
    intervals: List[SuspiciousInterval] = Field(...)
    path_processed: Optional[str] = None
    class Config:
        from_attributes = True
        json_encoders = {
            uuid.UUID: str
        }