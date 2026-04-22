import logging
import uuid
import pytest
import requests

from config import BACKEND_URL
from database import (
    gen_sample_student, add_students, gen_sample_recording, add_recordings,
    gen_sample_suspicious_intervals, add_suspicious_intervals
)

def add_sample_intervals(count: int):
    student = add_students([gen_sample_student()])[0]
    recording = add_recordings([gen_sample_recording(student["student_id"])])[0]
    intervals = add_suspicious_intervals(gen_sample_suspicious_intervals(count, recording["recording_id"]))
    return intervals, recording["recording_id"]
    
def test_get_intervals(test_env):
    intervals, recording_id = add_sample_intervals(5)

    logging.info("GET suspicious/{id}")
    response = requests.get(f"{BACKEND_URL}/suspicious/{recording_id}", timeout=10)
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 5

    for i in range(5):
        assert([ x == intervals[i] for x in data ])
