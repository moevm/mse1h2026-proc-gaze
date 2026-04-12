"""
Integration tests for student API endpoints.
"""

import logging
import uuid

import pytest
import requests

from config import BACKEND_URL
from database import dump_db

logger = logging.getLogger(__name__)

SAMPLE_STUDENT_DATA = {
    "first_name": "Ivan",
    "last_name": "Ivanov",
    "patronymic": "Ivanovich",
    "group": "3384",
}

def test_create_student(test_env):
    logger.info("POST /students")
    response = requests.post(
        f"{BACKEND_URL}/students",
        json=SAMPLE_STUDENT_DATA,
        timeout=10
    )

    assert response.status_code == 201
    data = response.json()

    try:
        uuid.UUID(data["student_id"])
    except ValueError as e:
        pytest.fail(f"Invalid student_id: {e}")

    data_copy = data.copy()
    del data_copy["student_id"]
    assert data_copy == SAMPLE_STUDENT_DATA

    db = dump_db()
    assert data in db["students"]
