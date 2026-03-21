import asyncio
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi import status

import aiofiles

from src.util.rabbit import AMQP_QUEUE, AMQP_RESULT_QUEUE, DATA_DIR
from src.util import rabbit
from src.consumers.tracking_consumer import handle_tracking_result

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Подключение к RabbitMQ и запуск потребителя."""
    await rabbit.connect()
    consumer_task = asyncio.create_task(
        rabbit.consume(AMQP_RESULT_QUEUE, handle_tracking_result)
    )
    logger.info("RabbitMQ consumer started on queue: %s", AMQP_RESULT_QUEUE)
    yield
    consumer_task.cancel()
    await rabbit.disconnect()


app = FastAPI(lifespan=lifespan)


@app.post("/upload")
async def handle_upload_files(
    webcam: UploadFile = File(None),
    screencast: UploadFile = File(None),
):
    """Загрузка видео с веб-камеры и скринкаста, отправка задания в очередь трекера."""
    if webcam is None or screencast is None:
        return JSONResponse(
            content={"error": "Expected 'webcam' and 'screencast' files."},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    job_id = str(uuid.uuid4())

    upload_dir = DATA_DIR / "uploads" / job_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    webcam_path = f"uploads/{job_id}/webcam_{webcam.filename}"
    screencast_path = f"uploads/{job_id}/screencast_{screencast.filename}"

    async with aiofiles.open(DATA_DIR / webcam_path, "wb") as f:
        while chunk := await webcam.read(1024 * 1024):
            await f.write(chunk)

    async with aiofiles.open(DATA_DIR / screencast_path, "wb") as f:
        while chunk := await screencast.read(1024 * 1024):
            await f.write(chunk)

    await rabbit.publish(
        AMQP_QUEUE,
        {
            "job_id": job_id,
            "inputs": {
                "screen_video": screencast_path,
                "webcam_video": webcam_path,
            },
        },
    )

    logger.info("Job %s published to %s", job_id, AMQP_QUEUE)

    return JSONResponse(
        content={"job_id": job_id},
        status_code=status.HTTP_200_OK,
    )
