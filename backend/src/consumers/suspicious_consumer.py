import logging
from datetime import datetime, timezone

from faststream.rabbit import RabbitQueue

from src.crud import notification_crud
from src.crud import suspicious_crud
from src.schemas.notification_schema import NotificationCreate
from src.schemas.suspicious_schema import SuspiciousResult
from src.util.broker import broker
from src.util.config import AMQP_RESULT_QUEUE

results_queue = RabbitQueue(AMQP_RESULT_QUEUE, durable=True)


@broker.subscriber(results_queue)
async def handle_suspicious_intervals(message: SuspiciousResult):
    logging.info(f"SuspiciousResult: {message}")
    await suspicious_crud.save_suspicious_intervals(message)
    await notification_crud.create_notification(
        NotificationCreate(
            recording_id=message.recording_id,
            created_date=datetime.now(timezone.utc),
            type="DONE",
        )
    )