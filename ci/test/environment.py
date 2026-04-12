from typing import Tuple
import logging
import subprocess
import requests
import os
import time
from datetime import datetime
import sys
import asyncio

# Add backend to path to import models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from src.models import Student, Recording, SuspiciousInterval, Notification
from src.schemas.student_schema import StudentRead
from src.schemas.recording_schema import RecordingRead
from src.schemas.suspicious_schema import SuspiciousRead
from src.schemas.notification_schema import NotificationRead

BACKEND_URL = "http://localhost:8000"
DATABASE_URL = "postgresql+asyncpg://gaze_user:password@localhost:5432/gaze_db"
TEST_LOGS_DIR = os.environ.get('TEST_LOGS_DIR')

logger = logging.getLogger(__name__)

def wait_for_backend_ready(max_retries=1000):
    for i in range(max_retries):
        try:
            response = requests.get(f"{BACKEND_URL}/docs")
            if response.status_code == 200:
                logging.info("Backend is ready!")
                return True
        except requests.exceptions.ConnectionError:
            logging.info("Backend is not ready yet.")
            time.sleep(1)
    return False


def dump_db():
    async def _dump_db_async():
        engine = create_async_engine(DATABASE_URL, echo=False)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            result_students = await session.execute(select(Student))
            students = result_students.scalars().all()
            students_json = [StudentRead.model_validate(student).model_dump(mode='json') for student in students]
            
            result_recordings = await session.execute(select(Recording))
            recordings = result_recordings.scalars().all()
            recordings_json = [RecordingRead.model_validate(recording).model_dump(mode='json') for recording in recordings]
            
            result_suspicious = await session.execute(select(SuspiciousInterval))
            suspicious_intervals = result_suspicious.scalars().all()
            suspicious_intervals_json = [SuspiciousRead.model_validate(interval).model_dump(mode='json') for interval in suspicious_intervals]
            
            result_notifications = await session.execute(select(Notification))
            notifications = result_notifications.scalars().all()
            notifications_json = [NotificationRead.model_validate(notification).model_dump(mode='json') for notification in notifications]
            
            await engine.dispose()
            
            return {
                "students": students_json,
                "recordings": recordings_json,
                "suspicious_intervals": suspicious_intervals_json,
                "notifications": notifications_json
            }
    
    return asyncio.run(_dump_db_async())


def clear_db():
    async def _clear_db_async():
        engine = create_async_engine(DATABASE_URL, echo=False)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            from sqlalchemy import delete
            
            await session.execute(delete(SuspiciousInterval))
            await session.execute(delete(Notification))
            await session.execute(delete(Recording))
            await session.execute(delete(Student))
            await session.commit()
            await engine.dispose()
    
    return asyncio.run(_clear_db_async())


class Environment:
    def _run_cmd(self, cmd, expect_ok=True) -> Tuple[str, str]:
        r = subprocess.run(cmd)
        
        if expect_ok:
            assert r.returncode == 0

    def __init__(self):
        self.components = [
            "backend",
            "tracker",
            "frontend",
            "db",
            "rabbitmq"
        ]

    def __enter__(self):
        logger.info("Starting environment")
        self._run_cmd(["docker", "compose", "up", "-d"])
        
        logging.info("Waiting for backend")
        wait_for_backend_ready()
        
        logging.info("Clearing DB")
        clear_db()

        return self

    def _capture_logs(self):
        for component in self.components:
            log_file_path = os.path.join(TEST_LOGS_DIR, f"{component}.log")
            logger.info(f"Capturing logs for {component} to {log_file_path}")

            result = subprocess.run(
                ["docker", "compose", "logs", component],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            logs = result.stdout.decode() + result.stderr.decode()
            
            with open(log_file_path, 'w') as f:
                f.write(logs)

    def _kill_all_components(self):
        self._run_cmd([ "docker", "compose", "stop" ], expect_ok=False)
        self._run_cmd([ "docker", "compose", "rm", "-f"], expect_ok=False)

    def __exit__(self, exc_type, exc_value, traceback):
        self._capture_logs()
        self._kill_all_components()