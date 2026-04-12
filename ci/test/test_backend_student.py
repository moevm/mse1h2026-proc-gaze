import pytest
import requests
import uuid
import logging
from environment import Environment, BACKEND_URL, dump_db

@pytest.fixture
def sample_student_data():
    return {
        "first_name": "Ivan",
        "last_name": "Ivanov",
        "patronymic": "Ivanovich",
        "group": "3384"
    }


def test_create_student(sample_student_data):
    with Environment():
        logging.info("POST /students")
        response = requests.post(
            f"{BACKEND_URL}/students",
            json=sample_student_data
        )
        
        assert response.status_code == 201
        
        data: dict = response.json()
        
        db = dump_db()
        assert data in db["students"]
        
        try:
            uuid.UUID(data["student_id"])
        except ValueError:
            pytest.fail("Invalid student_id")

        del data["student_id"]
        assert data == sample_student_data