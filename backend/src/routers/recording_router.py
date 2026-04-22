import uuid
from typing import List

from fastapi import APIRouter, status, UploadFile, Form, File
from faststream.rabbit import RabbitQueue

from src.crud import calibration_crud
from src.crud import recording_crud
from src.schemas.calibration_schema import CalibrationData, CalibrationRead
from src.schemas.process_request_schema import ProcessRequest
from src.schemas.recording_schema import RecordingRead
from src.util.broker import broker
from src.util.config import AMQP_QUEUE, AMQP_CALIBRATION_QUEUE

jobs_queue = RabbitQueue(AMQP_QUEUE, durable=True)
jobs_calibration_queue = RabbitQueue(AMQP_CALIBRATION_QUEUE, durable=True)

router = APIRouter(prefix="/recording", tags=["recording"])


@router.post("/upload", response_model=RecordingRead)
async def handle_upload_files(
        student_id: uuid.UUID = Form(...),
        webcam: UploadFile = File(...),
        screencast: UploadFile = File(...),
):
    recording = await recording_crud.create_recording(student_id, webcam, screencast)
    calibration_result = None
    try:
        calibration_result = await calibration_crud.get_calibration_result(student_id)
    except Exception:
        pass

    process_request = ProcessRequest(
        recording_id=recording.recording_id,
        path_webcam=recording.path_webcam,
        path_screen=recording.path_screen,
        calibration_result=calibration_result
    )
    await broker.publish(process_request, jobs_queue)
    return recording


@router.post("/calibration", response_model=CalibrationRead)
async def handle_calibration(
        student_id: uuid.UUID = Form(...),
        calibration_data: str = Form(...),
        webcam: UploadFile = File(...),
        screencast: UploadFile = File(...)
):
    try:
        calibration_data = CalibrationData.model_validate_json(calibration_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid calibration_data JSON: {e}")

    webcam_path, screencast_path = await recording_crud.save_calibration_files(
        student_id,
        webcam,
        screencast)

    await broker.publish(
        CalibrationRead(student_id=student_id,
                        webcam_path=webcam_path,
                        screencast_path=screencast_path,
                        calibration_data=calibration_data), jobs_calibration_queue)



@router.get("/screen/{id}")
async def get_screencast(id: uuid.UUID):
    screencast = await recording_crud.get_screen(id)
    return screencast


@router.get("/webcam/{id}")
async def get_webcam(id: uuid.UUID):
    webcam = await recording_crud.get_webcam(id)
    return webcam


@router.get("/processed/webcam/{id}")
async def get_processed_webcam(id: uuid.UUID):
    return await recording_crud.get_processed_webcam(id)


@router.get("/processed/screen/{id}")
async def get_processed_screen(id: uuid.UUID):
    return await recording_crud.get_processed_screen(id)


@router.get("", response_model=List[RecordingRead])
async def get_recordings():
    recordings = await recording_crud.get_recordings()
    return recordings


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recording(id: uuid.UUID):
    await recording_crud.delete_recording(id)
