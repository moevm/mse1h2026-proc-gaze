import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Callable, Coroutine

import aio_pika
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel

logger = logging.getLogger(__name__)

AMQP_URL = os.environ.get("AMQP_URL", "amqp://guest:guest@rabbitmq:5672/")
AMQP_QUEUE = os.environ.get("AMQP_QUEUE", "tracking.jobs")
AMQP_RESULT_QUEUE = os.environ.get("AMQP_RESULT_QUEUE", "tracking.results")
DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))

_connection: AbstractRobustConnection | None = None
_channel: AbstractRobustChannel | None = None


async def connect() -> None:
    """Подключение к RabbitMQ с повторными попытками и объявление очередей."""
    global _connection, _channel

    while True:
        try:
            _connection = await aio_pika.connect_robust(AMQP_URL)
            break
        except Exception as e:
            logger.warning("RabbitMQ not ready: %s. Retry in 2s...", e)
            await asyncio.sleep(2)

    _channel = await _connection.channel()
    await _channel.set_qos(prefetch_count=1)
    await _channel.declare_queue(AMQP_QUEUE, durable=True)
    await _channel.declare_queue(AMQP_RESULT_QUEUE, durable=True)
    logger.info("Connected to RabbitMQ at %s", AMQP_URL)


async def disconnect() -> None:
    """Закрытие соединения с RabbitMQ."""
    global _connection, _channel
    if _connection and not _connection.is_closed:
        await _connection.close()
    _connection = None
    _channel = None
    logger.info("Disconnected from RabbitMQ")


async def publish(queue_name: str, payload: dict[str, Any]) -> None:
    """Отправка JSON-сообщения в указанную очередь."""
    if _channel is None:
        raise RuntimeError("RabbitMQ is not connected")

    await _channel.default_exchange.publish(
        aio_pika.Message(
            body=json.dumps(payload).encode("utf-8"),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        ),
        routing_key=queue_name,
    )
    logger.info("Published message to %s: job_id=%s", queue_name, payload.get("job_id"))


async def consume(
    queue_name: str,
    callback: Callable[[dict[str, Any]], Coroutine],
) -> None:
    """Запуск потребителя сообщений из очереди. Работает бесконечно."""
    if _channel is None:
        raise RuntimeError("RabbitMQ is not connected")

    queue = await _channel.declare_queue(queue_name, durable=True)

    async with queue.iterator() as it:
        async for message in it:
            async with message.process(requeue=False):
                try:
                    payload = json.loads(message.body.decode("utf-8"))
                    await callback(payload)
                except Exception:
                    logger.exception("Error processing message from %s", queue_name)
