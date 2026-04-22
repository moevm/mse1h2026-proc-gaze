import logging
import uuid
import pytest
import requests

from config import BACKEND_URL
from database import dump_db, gen_sample_students, add_students, gen_sample_recordings, add_recordings

def add_sample_recordings(count: int):
    student = add_students(gen_sample_students(1))[0]
    recordings = add_recordings(gen_sample_recordings(count, student["student_id"]))
    return recordings

def test_delete_recording(test_env):
    add_sample_recordings(5)

    db_old = dump_db()
    assert len(db_old["recordings"]) == 5
    to_delete = db_old["recordings"][3]
    logging.info(f"Will delete recording: {to_delete}")

    logging.info("DELETE /{id}")
    response = requests.delete(f"{BACKEND_URL}/recording/{to_delete['recording_id']}", timeout=10)
    assert response.status_code == 204

    db_new = dump_db()
    assert db_old["recordings"][0] in db_new["recordings"]
    assert db_old["recordings"][1] in db_new["recordings"]
    assert db_old["recordings"][2] in db_new["recordings"]
    assert db_old["recordings"][3] not in db_new["recordings"]
    assert db_old["recordings"][4] in db_new["recordings"]
    

def test_get_all_recordings(test_env):
    N_SAMPLE_RECORDINGS=5
    recordings = add_sample_recordings(N_SAMPLE_RECORDINGS)

    logging.info("GET /recording")
    response = requests.get(f"{BACKEND_URL}/recording", timeout=10)
    assert response.status_code == 200

    data = response.json()
    assert len(recordings) == N_SAMPLE_RECORDINGS

    for i in range(N_SAMPLE_RECORDINGS):
        logging.info(f"Recv {data[i]}")
        
    for i in range(N_SAMPLE_RECORDINGS):
        assert any([ x == recordings[i] for x in data ])