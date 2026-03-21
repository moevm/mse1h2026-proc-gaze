import logging

from src.crud import notification_crud
from src.crud import suspicious_crud
from src.schemas.suspicious_schema import SuspiciousResult
from src.util.broker import broker
from src.util.config import AMQP_RESULT_QUEUE


@broker.subscriber(AMQP_RESULT_QUEUE)
async def handle_suspicious_intervals(message: SuspiciousResult):
    logging.info(f"SuspiciousResult: {message}")
    await suspicious_crud.save_suspicious_intervals(message)
    await notification_crud.create_notification()