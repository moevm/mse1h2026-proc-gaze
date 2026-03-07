import uuid
from datetime import datetime, time, timezone
from enum import Enum as PyEnum

from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Enum, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base


class RecordingStatus(PyEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class NotificationType(PyEnum):
    DONE = "DONE"


class Student(Base):
    __tablename__ = "student"

    student_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    recordings = relationship("Recording", back_populates="student")

    def __repr__(self):
        return f"<Student(student_id={self.student_id})>"


class Recording(Base):
    __tablename__ = "recording"

    recording_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id   = Column(UUID(as_uuid=True), ForeignKey("student.student_id", ondelete="CASCADE"), nullable=False)

    path_screen     = Column(String(255), nullable=False)
    path_webcam     = Column(String(255), nullable=False)
    path_processed  = Column(String(255), nullable=True)
    created_date    = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    status          = Column(Enum(RecordingStatus), default=RecordingStatus.PENDING, nullable=False)
    processed_date  = Column(DateTime, nullable=True)
    suspicion_level = Column(Float, nullable=True)

    student              = relationship("Student", back_populates="recordings")
    suspicious_intervals = relationship("SuspiciousInterval", back_populates="recording")
    notifications        = relationship("Notification", back_populates="recording")

    def __repr__(self):
        return f"<Recording(recording_id={self.recording_id})>"


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


class Notification(Base):
    __tablename__ = "notification"

    notification_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recording_id    = Column(UUID(as_uuid=True), ForeignKey("recording.recording_id", ondelete="CASCADE"), nullable=False)
    
    created_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    sent_date    = Column(DateTime, nullable=True)
    type         = Column(Enum(NotificationType), nullable=False)

    recording = relationship("Recording", back_populates="notifications")

    def __repr__(self):
        return f"<Notification(notification_id={self.notification_id})>"
