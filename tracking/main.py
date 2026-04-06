import asyncio
import logging
import os
import traceback
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

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
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
    tracker.gaze_mapper.eval()
    tracker.gaze_mapper.to(device)
    logger.info("Tracker ready, waiting for messages...")


@broker.subscriber(jobs_queue)
async def handle_job(message: dict[str, Any]):
    try:
        with torch.no_grad():
            result = await asyncio.to_thread(tracker.process_job, message)
    except Exception as error:
        recording_id = message.get("recording_id") if isinstance(message, dict) else None
        logger.exception("Error processing recording %s", recording_id)
        result = {
            "recording_id": str(recording_id) if recording_id else None,
            "intervals": [],
        }

    await broker.publish(result, queue=results_queue)


async def main():
    while True:
        try:
            await broker.start()
            logger.info(f"RabbitMQ broker started at url: {AMQP_URL}")
            break
        except Exception as e:
            logger.warning(f"RabbitMQ not ready: {e}. Retry in 2s...")
            await asyncio.sleep(2)
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
