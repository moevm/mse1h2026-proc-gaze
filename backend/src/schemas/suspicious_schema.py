import uuid
from typing import Optional

from pydantic import BaseModel, computed_field
from datetime import time

class SuspiciousRead(BaseModel):
    sus_id: uuid.UUID
    recording_id: uuid.UUID
    time: time
    duration: float
    description: str

    class Config:
        from_attributes = True
        json_encoders = {
            uuid.UUID: str,
            time: lambda v: v.isoformat() if v else None
        }

    @computed_field
    @property
    def end_time(self) -> Optional[str]:
        if self.time and self.duration:
            return f"{self.time.isoformat()} + {self.duration}s"
        return None

    @computed_field
    @property
    def summary(self) -> str:
        return f"Suspicious interval at {self.time} lasting {self.duration}s"