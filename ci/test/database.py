import logging
import sys
from datetime import time
from typing import Dict, List
import uuid
from faker import Faker
import random

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

sys.path.insert(0, str("backend"))

from src.models import Notification, Recording, Student, SuspiciousInterval, RecordingStatus, NotificationType
from src.schemas.notification_schema import NotificationRead
from src.schemas.recording_schema import RecordingRead
from src.schemas.student_schema import StudentRead
from src.schemas.suspicious_schema import SuspiciousRead

from config import DATABASE_URL

_engine = None

fake = Faker("ru_RU")

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
        logging.info("Database cleared")
    except Exception as e:
        session.rollback()
        raise Exception(f"Failed to clear database: {e}") from e
    finally:
        session.close()

    
def gen_sample_student(have_patronymic: bool = True):
    full_name = fake.name().split()
    GROUPS = [ "3381", "3383", "3384", "3385", "3388",
               "4381", "4383", "4384", "4385", "4388" ]
    
    return {
        "first_name": full_name[1],
        "last_name": full_name[0],
        "patronymic": full_name[2] if have_patronymic else None,
        "group": random.choice(GROUPS)
    }


def gen_sample_recording(student_id: uuid.uuid4, status: RecordingStatus = RecordingStatus.DONE):
    recording_id = uuid.uuid4()
    result = {
        "student_id": student_id,
        "recording_id": recording_id,
        "path_screen": f"/recordings/screen/{recording_id}.mp4",
        "path_webcam": f"/recordings/webcam/{recording_id}.mp4",
        "status": status
    }

    if status == RecordingStatus.DONE:
        result["path_processed_screen"] = f"/recordings/processed/screen/{recording_id}.mp4"
        result["path_processed_webcam"] = f"/recordings/processed/webcam/{recording_id}.mp4"
        result["suspicion_level"]       = random.random()
    
    return result


def gen_sample_suspicious_interval(recording_id: uuid.uuid4):
    DESCRIPTIONS = [
        "Looking away from screen",
        "Multiple people detected",
        "LLM usage detected",
        "Major skill issue detected"
    ]
    
    return {
        "recording_id": recording_id,
        "time": time(random.randint(0, 1), random.randrange(0, 60), random.randrange(0, 60)),
        "duration": random.randrange(0, 30),
        "description": random.choice(DESCRIPTIONS)
    }


def gen_sample_notification(recording_id: uuid.uuid4):
    return {
        "recording_id": recording_id,
        "type": NotificationType.DONE
    }


def gen_sample_students(count: int, have_patronymic: bool = True):
    return [ gen_sample_student(have_patronymic=have_patronymic) for _ in range(count) ]

def gen_sample_recordings(count: int, student_id: uuid.uuid4, status: RecordingStatus = RecordingStatus.DONE):
    return [ gen_sample_recording(student_id=student_id, status=status) for _ in range(count) ]

def gen_sample_suspicious_intervals(count: int, recording_id: uuid.uuid4):
    return [ gen_sample_suspicious_interval(recording_id=recording_id) for _ in range(count) ]

def gen_sample_notifications(count: int, recording_id: uuid.uuid4):
    return [ gen_sample_notification(recording_id=recording_id) for _ in range(count) ]


def add_to_db(type: any, type_read: any, objects: List[Dict]):
    session = get_db_session()
    try:
        added_objects = []
        result = []
        for data in objects:
            obj = type(**data)
            session.add(obj)
            added_objects.append(obj)
        session.commit()

        logging.info(f"Added {len(added_objects)} {type.__name__}(s)")
        for obj in added_objects:
            session.refresh(obj)
            obj_json = type_read.model_validate(obj).model_dump(mode="json")
            logging.info(obj_json)
            result.append(obj_json)
        return result
    except Exception as e:
        session.rollback()
        raise Exception(f"Failed to add sample {type.__name__}(s): {e}") from e
    finally:
        session.close()

def add_students(students: List[Dict]) -> List[Student]:
    return add_to_db(Student, StudentRead, students)

def add_recordings(recordings: List[Dict]) -> List[Recording]:
    return add_to_db(Recording, RecordingRead, recordings)

def add_suspicious_intervals(intervals: List[Dict]) -> List[SuspiciousInterval]:
    return add_to_db(SuspiciousInterval, SuspiciousRead, intervals)

def add_notifications(notifications: List[Dict]) -> List[Notification]:
    return add_to_db(Notification, NotificationRead, notifications)