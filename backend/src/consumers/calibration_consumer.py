import logging
from datetime import datetime, timezone

from faststream.rabbit import RabbitQueue

from src.models import NotificationType
from src.schemas.notification_schema import NotificationCreate
from src.crud import notification_crud
from src.schemas.calibration_schema import CalibrationResultRead
from src.crud import calibration_crud
from src.util.broker import broker
from src.util.config import AMQP_CALIBRATION_RESULT_QUEUE

calibration_results_queue = RabbitQueue(AMQP_CALIBRATION_RESULT_QUEUE, durable=True)


@broker.subscriber(calibration_results_queue)
async def handle_calibration_result(message: CalibrationResultRead):
    logging.info(f"Calibration result: {message}")
    await calibration_crud.create_calibration_result(message)

