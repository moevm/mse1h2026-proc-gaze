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

SAMPLE_STUDENT_DATA_2 = {
    "first_name": "Petr",
    "last_name": "Petrov",
    "patronymic": "Petrovich",
    "group": "3385",
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


def test_get_student(test_env):
    logger.info("GET /students/{id}")

    # Create student
    create_response = requests.post(
        f"{BACKEND_URL}/students",
        json=SAMPLE_STUDENT_DATA,
        timeout=10
    )
    assert create_response.status_code == 201
    student_id = create_response.json()["student_id"]

    # Get student
    response = requests.get(
        f"{BACKEND_URL}/students/{student_id}",
        timeout=10
    )
    assert response.status_code == 200

    data = response.json()
    assert data["student_id"] == student_id
    assert data["first_name"] == SAMPLE_STUDENT_DATA["first_name"]
    assert data["last_name"]  == SAMPLE_STUDENT_DATA["last_name"]
    assert data["patronymic"] == SAMPLE_STUDENT_DATA["patronymic"]
    assert data["group"]      == SAMPLE_STUDENT_DATA["group"]


def test_get_all_students(test_env):
    logger.info("GET /students")

    # Create two students
    requests.post(f"{BACKEND_URL}/students", json=SAMPLE_STUDENT_DATA, timeout=10)
    requests.post(f"{BACKEND_URL}/students", json=SAMPLE_STUDENT_DATA_2, timeout=10)

    # Get all students
    response = requests.get(f"{BACKEND_URL}/students", timeout=10)
    assert response.status_code == 200

    students = response.json()
    assert len(students) == 2

    del students[0]["student_id"]
    del students[1]["student_id"]
    assert any([ x == SAMPLE_STUDENT_DATA for x in students])
    assert any([ x == SAMPLE_STUDENT_DATA_2 for x in students])

def test_get_nonexistent_student(test_env):
    logger.info("GET /students/{id} with non-existent ID")

    fake_id = str(uuid.uuid4())
    response = requests.get(f"{BACKEND_URL}/students/{fake_id}", timeout=10)
    assert response.status_code == 404

def test_create_student_no_patr(test_env):
    logger.info("POST /students without patronymic")
    data = {
        "first_name": "Sergey",
        "last_name": "Sergeev",
        "patronymic": None,
        "group": "3384",
    }

    response = requests.post(f"{BACKEND_URL}/students", json=data, timeout=10)
    assert response.status_code == 201

    result = response.json()
    assert result["patronymic"] is None