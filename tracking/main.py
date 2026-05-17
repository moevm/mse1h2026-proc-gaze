import asyncio
import logging
import os
from typing import Any
import torch

from faststream import FastStream
from faststream.rabbit import RabbitBroker, RabbitQueue

from src.tracker import Tracker

logging.basicConfig(level=logging.INFO,
                    format="%(name)s | %(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

AMQP_URL = os.environ["AMQP_URL"]
JOBS_Q = os.environ.get("AMQP_QUEUE", "tracking.jobs")
RESULTS_Q = os.environ.get("AMQP_RESULT_QUEUE", "tracking.results")

CALIBRATION_JOBS_Q = os.environ.get("AMQP_CALIBRATION_QUEUE", "tracking.calibration.jobs")
CALIBRATION_RESULTS_Q = os.environ.get("AMQP_CALIBRATION_RESULT_QUEUE", "tracking.calibration.results")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
broker = RabbitBroker(AMQP_URL)
app = FastStream(broker)

jobs_queue = RabbitQueue(JOBS_Q, durable=True)
results_queue = RabbitQueue(RESULTS_Q, durable=True)
calibration_jobs_queue = RabbitQueue(CALIBRATION_JOBS_Q, durable=True)
calibration_results_queue = RabbitQueue(CALIBRATION_RESULTS_Q, durable=True)

tracker: Tracker | None = None
tracker_lock: asyncio.Lock | None = None


@app.on_startup
async def on_startup():
    global tracker, tracker_lock
    logger.info("Loading tracker...")
    tracker = Tracker(use_torch_gaze=True)
    tracker.gaze_mapper.eval()
    tracker.gaze_mapper.to(device)
    tracker_lock = asyncio.Lock()
    logger.info("Tracker ready, waiting for messages...")


@broker.subscriber(jobs_queue)
async def handle_job(message: dict[str, Any]):
    try:
        if tracker is None or tracker_lock is None:
            raise RuntimeError("Tracker is not initialized")
        async with tracker_lock:
            result = await asyncio.to_thread(tracker.process_job, message)
    except Exception:
        recording_id = message.get("recording_id") if isinstance(message, dict) else None
        logger.exception("Error processing recording %s", recording_id)
        result = {
            "recording_id": str(recording_id) if recording_id else None,
            "intervals": [],
        }

    await broker.publish(result, queue=results_queue)


@broker.subscriber(calibration_jobs_queue)
async def handle_calibration_job(message: dict[str, Any]):
    try:
        if tracker is None or tracker_lock is None:
            raise RuntimeError("Tracker is not initialized")
        async with tracker_lock:
            result = await asyncio.to_thread(tracker.process_calibration, message)
    except Exception:
        student_id = message.get("student_id") if isinstance(message, dict) else None
        logger.exception("Error processing calibration for student %s", student_id)
        return

    await broker.publish(result, queue=calibration_results_queue)


async def main():
    while True:
        try:
            logger.info(f"Starting RabbitMQ broker at url: {AMQP_URL}")
            await app.run()
            break
        except Exception as e:
            logger.warning(f"RabbitMQ not ready: {e}. Retry in 2s...")
            await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
