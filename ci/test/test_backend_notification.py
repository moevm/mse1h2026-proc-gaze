import logging
import uuid
import pytest
import requests

from config import BACKEND_URL
from database import (
    dump_db, gen_sample_students, add_students, gen_sample_recordings, add_recordings,
    add_notifications, gen_sample_notification
)

def add_sample_notifications(count: int):
    student = add_students(gen_sample_students(1))[0]
    recordings = add_recordings(gen_sample_recordings(count, student["student_id"]))
    
    notifications = []
    for recording in recordings:
        notifications.append(gen_sample_notification(recording["recording_id"]))
    
    return add_notifications(notifications)
    
def test_delete_notification(test_env):
    add_sample_notifications(5)

    db_old = dump_db()
    assert len(db_old["notifications"]) == 5
    to_delete = db_old["notifications"][3]
    logging.info(f"Will delete notification: {to_delete}")

    logging.info("DELETE notification/{id}")
    response = requests.delete(f"{BACKEND_URL}/notification/{to_delete['notification_id']}", timeout=10)
    assert response.status_code == 204

    db_new = dump_db()
    assert db_old["notifications"][0] in db_new["notifications"]
    assert db_old["notifications"][1] in db_new["notifications"]
    assert db_old["notifications"][2] in db_new["notifications"]
    assert db_old["notifications"][3] not in db_new["notifications"]
    assert db_old["notifications"][4] in db_new["notifications"]
    

# TODO: fix
"""
def test_get_all_notifications(test_env):
    N_SAMPLE_NOTIFICATIONS=5
    notifications = add_sample_notifications(N_SAMPLE_NOTIFICATIONS)

    logging.info("GET /notification")
    response = requests.get(f"{BACKEND_URL}/notification", timeout=10)
    assert response.status_code == 200

    data = response.json()
    assert len(notifications) == N_SAMPLE_NOTIFICATIONS

    for i in range(N_SAMPLE_NOTIFICATIONS):
        logging.info(f"Recv {data[i]}")
        
    for i in range(N_SAMPLE_NOTIFICATIONS):
        assert any([ x == notifications[i] for x in data ])
"""