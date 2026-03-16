import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class NotificationType(Enum):
    DONE = "DONE"


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
