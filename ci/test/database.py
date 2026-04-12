import logging
import sys
from pathlib import Path
from typing import Dict, List

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

sys.path.insert(0, str("backend"))

from src.models import Notification, Recording, Student, SuspiciousInterval
from src.schemas.notification_schema import NotificationRead
from src.schemas.recording_schema import RecordingRead
from src.schemas.student_schema import StudentRead
from src.schemas.suspicious_schema import SuspiciousRead

from config import DATABASE_URL

logger = logging.getLogger(__name__)

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
    return _engine


def get_db_session() -> Session:
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def dump_db() -> Dict[str, List[Dict]]:
    session = get_db_session()
    try:
        students = session.query(Student).all()
        students_json = [
            StudentRead.model_validate(student).model_dump(mode="json")
            for student in students
        ]

        recordings = session.query(Recording).all()
        recordings_json = [
            RecordingRead.model_validate(recording).model_dump(mode="json")
            for recording in recordings
        ]

        suspicious_intervals = session.query(SuspiciousInterval).all()
        suspicious_intervals_json = [
            SuspiciousRead.model_validate(interval).model_dump(mode="json")
            for interval in suspicious_intervals
        ]

        notifications = session.query(Notification).all()
        notifications_json = [
            NotificationRead.model_validate(notification).model_dump(mode="json")
            for notification in notifications
        ]

        return {
            "students": students_json,
            "recordings": recordings_json,
            "suspicious_intervals": suspicious_intervals_json,
            "notifications": notifications_json,
        }
    finally:
        session.close()


def clear_db() -> None:
    session = get_db_session()
    try:
        session.query(Notification).delete()
        session.query(SuspiciousInterval).delete()
        session.query(Recording).delete()
        session.query(Student).delete()
        session.commit()
        logger.info("Database cleared")
    except Exception as e:
        session.rollback()
        raise Exception(f"Failed to clear database: {e}") from e
    finally:
        session.close()
