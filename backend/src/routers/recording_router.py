from typing import List

from fastapi import APIRouter, status, UploadFile, Form, File

from faststream.rabbit import RabbitQueue

from src.schemas.process_request_schema import ProcessRequest
from src.schemas.recording_schema import RecordingRead
from src.crud import recording_crud
from src.util.broker import broker
from src.util.config import AMQP_QUEUE

jobs_queue = RabbitQueue(AMQP_QUEUE, durable=True)

router = APIRouter(prefix="/recording", tags=["recording"])


@router.post("/upload", response_model=RecordingRead)
async def handle_upload_files(
        student_id: str = Form(...),
        webcam: UploadFile = File(...),
        screencast: UploadFile = File(...)
):
    recording = await recording_crud.create_recording(student_id, webcam, screencast)
    process_request = ProcessRequest.model_validate(recording)
    await broker.publish(process_request, jobs_queue)
    return recording


@router.get("/screen/{id}")
async def get_screencast(id: str):
    screencast = await recording_crud.get_screen(id)
    return screencast


@router.get("/webcam/{id}")
async def get_webcam(id: str):
    webcam = await recording_crud.get_webcam(id)
    return webcam


@router.get("", response_model=List[RecordingRead])
async def get_recordings():
    recordings = await recording_crud.get_recordings()
    return recordings


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recording(id: str):
    await recording_crud.delete_recording(id)
