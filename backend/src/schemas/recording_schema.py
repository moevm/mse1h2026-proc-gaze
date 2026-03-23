from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from src.models import RecordingStatus


class RecordingRead(BaseModel):
    recording_id: UUID
    student_id: UUID
    path_screen: str
    path_webcam: str
    path_processed_webcam: Optional[str] = None
    path_processed_screen: Optional[str] = None
    created_date: datetime
    status: RecordingStatus
    processed_date: Optional[datetime] = None
    suspicion_level: Optional[float] = None

    model_config = {"from_attributes": True}