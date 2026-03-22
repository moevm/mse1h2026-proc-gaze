import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Enum, Time, Boolean, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.util.database import Base


class RecordingStatus(PyEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class NotificationType(PyEnum):
    DONE = "DONE"


class Student(Base):
    __tablename__ = "student"

    student_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    patronymic = Column(String(255), nullable=False)
    group = Column(String(255), nullable=False)
    recordings = relationship("Recording", back_populates="student")

    def __repr__(self):
        return f"<Student(student_id={self.student_id})>"
    
    def to_dict(self):
        return {
            "student_id": str(self.student_id)
        }


class Recording(Base):
    __tablename__ = "recording"

    recording_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id   = Column(UUID(as_uuid=True), ForeignKey("student.student_id", ondelete="CASCADE"), nullable=False)

    path_screen     = Column(String(255), nullable=False)
    path_webcam     = Column(String(255), nullable=False)
    path_processed  = Column(String(255), nullable=True)
    created_date    = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    status          = Column(Enum(RecordingStatus), default=RecordingStatus.PENDING, nullable=False)
    processed_date  = Column(TIMESTAMP(timezone=True), nullable=True)
    suspicion_level = Column(Float, nullable=True)

    student              = relationship("Student", back_populates="recordings")
    suspicious_intervals = relationship("SuspiciousInterval", back_populates="recording")
    notifications        = relationship("Notification", back_populates="recording")

    def __repr__(self):
        return f"<Recording(recording_id={self.recording_id})>"
    
    def to_dict(self):
        return {
            "recording_id": str(self.recording_id),
            "student_id": str(self.student_id),
            "path_screen": self.path_screen,
            "path_webcam": self.path_webcam,
            "path_processed": self.path_processed,
            "created_date": self.created_date.isoformat() if self.created_date else None,
            "status": self.status.value if self.status else None,
            "processed_date": self.processed_date.isoformat() if self.processed_date else None,
            "suspicion_level": self.suspicion_level
        }


class SuspiciousInterval(Base):
    __tablename__ = "suspicious_interval"

    sus_id       = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recording_id = Column(UUID(as_uuid=True), ForeignKey("recording.recording_id", ondelete="CASCADE"), nullable=False)
    
    time        = Column(Time, nullable=False)
    duration    = Column(Float, nullable=False)
    description = Column(String(500), nullable=False)

    recording = relationship("Recording", back_populates="suspicious_intervals")

    def __repr__(self):
        return f"<SuspiciousInterval(sus_id={self.sus_id})>"
    
    def to_dict(self):
        return {
            "sus_id": str(self.sus_id),
            "recording_id": str(self.recording_id),
            "time": self.time.isoformat() if self.time else None,
            "duration": self.duration,
            "description": self.description
        }


class Notification(Base):
    __tablename__ = "notification"

    notification_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recording_id    = Column(UUID(as_uuid=True), ForeignKey("recording.recording_id", ondelete="CASCADE"), nullable=False)
    
    created_date = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    sent_date    = Column(DateTime, nullable=True)
    type         = Column(Enum(NotificationType), nullable=False)

    recording = relationship("Recording", back_populates="notifications")
    def __repr__(self):
        return f"<Notification(notification_id={self.notification_id})>"
    
    def to_dict(self):
        return {
            "notification_id": str(self.notification_id),
            "recording_id": str(self.recording_id),
            "created_date": self.created_date.isoformat() if self.created_date else None,
            "sent_date": self.sent_date.isoformat() if self.sent_date else None,
            "type": self.type.value if self.type else None
        }
