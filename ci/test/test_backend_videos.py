import logging
import uuid
import requests
import re
import time

from config import BACKEND_URL, TEST_LOGS_DIR
from database import gen_sample_student, add_students, dump_db
from docker import docker_exec

def wait_for_200(url: str, attempts: int = 100):
    logging.info(f"Waiting for OK response at {url}")

    for i in range(attempts):
        time.sleep(1)
        response = requests.get(url)
        if response.status_code == 200:
            logging.info(f"{url} -> OK")
            return response
        else:
            logging.info(f"Not yet ({i+1}/{attempts}). Detail: {response.json()}")
    
    raise TimeoutError(f"Failed to wait at {url}")

def expect_same(filename1: str, filename2: str):
    assert open(filename1, 'rb').read() == open(filename2, 'rb').read()

def ls_shared_data():
    result: str = docker_exec([ "/bin/sh", "-c", "ls -1 /data/" ]).strip()
    
    if len(result) == 0:
        logging.info(f"ls shared data is empty")
    else:
        logging.info(f"ls shared data: " + ', '.join([ f"'{x}'" for x in result.splitlines()]))
    
    return result.splitlines()

def test_video_upload(test_env):
    student = add_students([gen_sample_student()])[0]

    form = {
        'student_id': (None, student['student_id']),
        'webcam': ('webcam.mp4', open('assets/test-webcam-5s.mp4', 'rb'), 'video/mp4'),
        'screencast': ('screen.mp4', open('assets/test-screen-5s.mp4', 'rb'), 'video/mp4'),
    }

    ls = ls_shared_data()
    assert len(ls) == 0
    
    logging.info("POST /recording/upload")
    response = requests.post(f"{BACKEND_URL}/recording/upload", files=form)
    assert response.status_code == 200

    data = response.json()
    logging.info(f"Recv {data}")

    try:
        uuid.UUID(data["recording_id"])
    except Exception as e:
        logging.error("Invalid recording_id")
        raise e

    recording_id = data["recording_id"]

    assert str(data["student_id"]) == str(student["student_id"])
    assert re.match(f".+/.+_screencast\\.mp4", data["path_screen"])
    assert re.match(f".+/.+_webcam\\.mp4", data["path_webcam"])
    assert data["path_processed_screen"] is None
    assert data["path_processed_webcam"] is None
    assert data["created_date"] is not None
    assert data["processed_date"] is None
    assert data["suspicion_level"] is None
    assert data["count_suspicions"] == 0
    assert data["status"] == "PENDING"

    logging.info("GET /recording/screen/{id}")
    response = requests.get(f"{BACKEND_URL}/recording/screen/{recording_id}")
    assert response.status_code == 200

    with open(TEST_LOGS_DIR + "/recv-screen.mp4", "wb") as file:
        file.write(response.content)

    logging.info("GET /recording/webcam/{id}")
    response = requests.get(f"{BACKEND_URL}/recording/webcam/{recording_id}")
    assert response.status_code == 200

    with open(TEST_LOGS_DIR + "/recv-webcam.mp4", "wb") as file:
        file.write(response.content)

    expect_same('assets/test-screen-5s.mp4', TEST_LOGS_DIR + "/recv-screen.mp4")
    expect_same('assets/test-webcam-5s.mp4', TEST_LOGS_DIR + "/recv-webcam.mp4")
    
    response = wait_for_200(f"{BACKEND_URL}/recording/processed/webcam/{recording_id}")
    response = wait_for_200(f"{BACKEND_URL}/recording/processed/screen/{recording_id}")

    db = dump_db()
    db_recording = [ x for x in db["recordings"] if x["recording_id"] == recording_id ]
    assert len(db_recording) == 1
    db_recording = db_recording[0]

    assert db_recording["status"] == "DONE"
    assert db_recording["processed_date"] is not None
    assert db_recording["path_processed_screen"] is not None
    assert db_recording["path_processed_webcam"] is not None

    ls = ls_shared_data()
    assert len(ls) == 2
    assert "results" in ls