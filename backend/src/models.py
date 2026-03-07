import uuid
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID

from .database import Base


class Recording(Base):
    __tablename__ = "recording"

    recording_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    def __repr__(self):
        return f"<Recording(recording_id={self.recording_id})>"