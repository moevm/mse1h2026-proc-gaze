import os
from pathlib import Path

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")
UPLOAD_DIR = Path(os.environ.get("DATA_DIR"))
if not UPLOAD_DIR.exists():
    raise ValueError("UPLOAD_DIR environment variable is not set or path is bad")

RMQ_URL = os.getenv("AMQP_URL")
if not RMQ_URL:
    raise ValueError("RMQ_URL environment variable is not set")

AMQP_QUEUE = os.getenv("AMQP_QUEUE")
if not AMQP_QUEUE:
    raise ValueError("AMQP_QUEUE environment variable is not set")


AMQP_RESULT_QUEUE = os.getenv("AMQP_RESULT_QUEUE")
if not AMQP_RESULT_QUEUE:
    raise ValueError("AMQP_RESULT_QUEUE environment variable is not set")

AMQP_CALIBRATION_QUEUE = os.getenv("AMQP_CALIBRATION_QUEUE")
if not AMQP_QUEUE:
    raise ValueError("AMQP_CALIBRATION_QUEUE environment variable is not set")

AMQP_CALIBRATION_RESULT_QUEUE = os.getenv("AMQP_CALIBRATION_RESULT_QUEUE")
if not AMQP_CALIBRATION_RESULT_QUEUE:
    raise ValueError("AMQP_CALIBRATION_RESULT_QUEUE environment variable is not set")


