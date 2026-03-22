import asyncio
import logging
import os
import traceback
from typing import Any

from faststream import FastStream
from faststream.rabbit import RabbitBroker, RabbitQueue

from src.tracker import Tracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AMQP_URL = os.environ["AMQP_URL"]
JOBS_Q = os.environ.get("AMQP_QUEUE", "tracking.jobs")
RESULTS_Q = os.environ.get("AMQP_RESULT_QUEUE", "tracking.results")

broker = RabbitBroker(AMQP_URL)
app = FastStream(broker)

jobs_queue = RabbitQueue(JOBS_Q, durable=True)
results_queue = RabbitQueue(RESULTS_Q, durable=True)

tracker: Tracker | None = None


@app.on_startup
async def on_startup():
    global tracker
    logger.info("Loading tracker...")
    tracker = Tracker()
    logger.info("Tracker ready, waiting for messages...")


@broker.subscriber(jobs_queue)
async def handle_job(message: dict[str, Any]):
    try:
        result = tracker.process_job(message)
    except Exception as error:
        recording_id = message.get("recording_id") if isinstance(message, dict) else None
        logger.exception("Error processing recording %s", recording_id)
        result = {
            "recording_id": str(recording_id) if recording_id else None,
            "intervals": [],
        }

    await broker.publish(result, queue=results_queue)


if __name__ == "__main__":
    asyncio.run(app.run())
