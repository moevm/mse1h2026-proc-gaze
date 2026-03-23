import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from src.models import NotificationType


class NotificationRead(BaseModel):
    notification_id: uuid.UUID
    recording_id: uuid.UUID
    created_date: datetime
    sent_date: Optional[datetime] = None
    type: NotificationType

    class Config:
        from_attributes = True
        json_encoders = {
            uuid.UUID: str,
            datetime: lambda v: v.isoformat() if v else None
        }

class NotificationCreate(BaseModel):
    recording_id: uuid.UUID
    created_date: datetime
    type: NotificationType