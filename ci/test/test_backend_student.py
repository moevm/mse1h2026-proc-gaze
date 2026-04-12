import logging
import uuid

import pytest
import requests

from config import BACKEND_URL
from database import dump_db, gen_sample_students, add_students

def test_create_student(test_env):
    student = gen_sample_students(1)[0]
    logging.info(f"Generated student: {student}")
    logging.info("POST /students")
    response = requests.post(f"{BACKEND_URL}/students", json=student, timeout=10)

    assert response.status_code == 201
    data = response.json()

    try:
        uuid.UUID(data["student_id"])
    except ValueError as e:
        pytest.fail(f"Invalid student_id: {e}")

    student["student_id"] = data["student_id"]
    assert data == student
    
    db = dump_db()
    assert data in db["students"]


def test_get_student(test_env):
    student = add_students(gen_sample_students(1))[0]
    
    logging.info("GET /students/{id}")
    response = requests.get(f"{BACKEND_URL}/students/{student['student_id']}", timeout=10)
    assert response.status_code == 200

    data = response.json()
    assert data["student_id"] == student["student_id"]
    assert data["first_name"] == student["first_name"]
    assert data["last_name"]  == student["last_name"]
    assert data["patronymic"] == student["patronymic"]
    assert data["group"]      == student["group"]


def test_get_all_students(test_env):
    N_STUDENTS=5
    students = add_students(gen_sample_students(N_STUDENTS))
    
    logging.info("GET /students")
    response = requests.get(f"{BACKEND_URL}/students", timeout=10)
    assert response.status_code == 200

    data = response.json()
    assert len(students) == N_STUDENTS

    for i in range(N_STUDENTS):
        logging.info(f"Recv {data[i]}")
        
    for i in range(N_STUDENTS):
        assert any([ x == students[i] for x in data ])

def test_get_nonexistent_student(test_env):
    logging.info("GET /students/{id} with non-existent ID")
    response = requests.get(f"{BACKEND_URL}/students/{uuid.uuid4()}", timeout=10)
    assert response.status_code == 404

def test_create_student_no_patr(test_env):
    logging.info("POST /students without patronymic")
    student = gen_sample_students(1, have_patronymic=False)[0]
    response = requests.post(f"{BACKEND_URL}/students", json=student, timeout=10)
    assert response.status_code == 201

    data = response.json()
    student["student_id"] = data["student_id"]
    assert data == student