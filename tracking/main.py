import asyncio
import json
import os
import traceback
from typing import Any

import aio_pika
from aio_pika.abc import AbstractRobustConnection

from src.tracker import Tracker

AMQP_URL = os.environ["AMQP_URL"]
JOBS_Q = os.environ.get("AMQP_QUEUE", "tracking.jobs")
RESULTS_Q = os.environ.get("AMQP_RESULT_QUEUE", "tracking.results")


def _decode_payload(body: bytes) -> dict[str, Any]:
    return json.loads(body.decode("utf-8"))


def _failed_result(body: bytes, error: Exception) -> dict[str, Any]:
    payload_job_id = None
    try:
        payload_job_id = _decode_payload(body).get("job_id")
    except Exception:
        pass

    return {
        "job_id": payload_job_id,
        "status": "FAILED",
        "error": "".join(traceback.format_exception(type(error), error, error.__traceback__)),
    }


async def _connect_amqp_with_retry() -> AbstractRobustConnection:
    while True:
        try:
            return await aio_pika.connect_robust(AMQP_URL)
        except Exception as error:
            print(f"RabbitMQ not ready for tracker: {error}. Retry in 2s...", flush=True)
            await asyncio.sleep(2)


async def main() -> None:
    conn = await _connect_amqp_with_retry()
    try:
        channel = await conn.channel()
        await channel.set_qos(prefetch_count=1)

        jobs_queue = await channel.declare_queue(JOBS_Q, durable=True)
        await channel.declare_queue(RESULTS_Q, durable=True)

        tracker = Tracker()

        async with jobs_queue.iterator() as it:
            async for message in it:
                async with message.process(requeue=False):
                    try:
                        payload = _decode_payload(message.body)
                        result = tracker.process_job(payload)
                    except Exception as error:
                        result = _failed_result(message.body, error)

                    await channel.default_exchange.publish(
                        aio_pika.Message(
                            body=json.dumps(result).encode("utf-8"),
                            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                        ),
                        routing_key=RESULTS_Q,
                    )
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
