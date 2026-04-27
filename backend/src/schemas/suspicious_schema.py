import uuid
from datetime import time as time_type
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class SuspiciousRead(BaseModel):
    sus_id: uuid.UUID = Field(...)
    recording_id: uuid.UUID = Field(...)
    time: time_type = Field(...)
    duration: float = Field(...)
    description: str = Field(...)

    class Config:
        from_attributes = True
        json_encoders = {
            uuid.UUID: str,
            time_type: lambda v: v.isoformat() if v else None
        }


class SuspiciousInterval(BaseModel):
    time: time_type = Field(...)
    duration: float = Field(...)
    description: str = Field(...)

    @field_validator("time", mode="before")
    @classmethod
    def parse_tracker_time(cls, value):
        if not isinstance(value, str):
            return value

        parts = value.split(":")
        if len(parts) != 3:
            return value

        try:
            hour = int(parts[0])
            minute = int(parts[1])
            second = float(parts[2])
        except ValueError:
            return value

        whole_second = int(second)
        microsecond = min(int(round((second - whole_second) * 1_000_000)), 999_999)
        try:
            return time_type(hour=hour, minute=minute, second=whole_second, microsecond=microsecond)
        except ValueError:
            return value

    class Config:
        from_attributes = True
        json_encoders = {
            time_type: lambda v: v.isoformat() if v else None
        }


class SuspiciousResult(BaseModel):
    recording_id: uuid.UUID = Field(...)
    intervals: List[SuspiciousInterval] = Field(...)
    path_processed_webcam: Optional[str] = None
    path_processed_screen: Optional[str] = None

    class Config:
        from_attributes = True
        json_encoders = {
            uuid.UUID: str
        }
