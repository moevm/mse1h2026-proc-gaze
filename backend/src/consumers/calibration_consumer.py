import logging

from faststream.rabbit import RabbitQueue

from src.crud import calibration_crud
from src.schemas.calibration_schema import CalibrationResultRead
from src.util.broker import broker
from src.util.config import AMQP_CALIBRATION_RESULT_QUEUE

calibration_results_queue = RabbitQueue(AMQP_CALIBRATION_RESULT_QUEUE, durable=True)


@broker.subscriber(calibration_results_queue)
async def handle_calibration_result(message: CalibrationResultRead):
    logging.info(f"Calibration result: {message}")
    await calibration_crud.create_calibration_result(message)
