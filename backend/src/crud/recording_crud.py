import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import UploadFile
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.exceptions import HTTPException

from src.schemas.recording_schema import RecordingRead
from src.models import Recording, SuspiciousInterval, RecordingStatus
from src.util.connection import connection
from src.util import file_storage
from pathlib import Path


@connection
async def get_recordings(session: AsyncSession):
    count_sub = (
        select(func.count(SuspiciousInterval.sus_id))
        .where(SuspiciousInterval.recording_id == Recording.recording_id)
        .scalar_subquery()
        .label("count_suspicions")
    )
    result = await session.execute(select(Recording, count_sub))
    rows = result.all()
    return [
        RecordingRead.model_validate({**recording.__dict__, "count_suspicions": count})
        for recording, count in rows
    ]


@connection
async def delete_recording(id: str, session: AsyncSession):
    try:
        recording_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid recording_id format. Expected UUID.")
    recording = (await session.execute(select(Recording).where(Recording.recording_id == recording_uuid))).scalar_one_or_none()
    if not recording:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recording not found")
    await session.delete(recording)
    await session.commit()


@connection
async def get_recording(id: str, session: AsyncSession):
    try:
        recording_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid recording_id format. Expected UUID.")
    recording = await session.execute(select(Recording).where(Recording.recording_id == recording_uuid))
    recording = recording.scalar_one_or_none()
    if recording is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"recording not found with uuid: {recording_uuid}")
    return recording


async def get_webcam(id: str):
    recording = await get_recording(id)
    return await file_storage.get_file(recording.path_webcam)


async def get_screen(id: str):
    recording = await get_recording(id)
    return await file_storage.get_file(recording.path_screen)


async def get_processed_webcam(id: str):
    recording = await get_recording(id)
    if not recording.path_processed_webcam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processed webcam video not ready yet")
    return await file_storage.get_file(recording.path_processed_webcam)


async def get_processed_screen(id: str):
    recording = await get_recording(id)
    if not recording.path_processed_screen:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processed screen video not ready yet")
    return await file_storage.get_file(recording.path_processed_screen)


@connection
async def create_recording(student_id: str,
                           webcam: UploadFile,
                           screencast: UploadFile, session: AsyncSession):
    if webcam is None or screencast is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Expected 'webcam' and 'screencast' files.")

    logging.info(
        f"student_id {student_id}, webcam type: {webcam.content_type}, screencast type: {screencast.content_type}")
    try:
        student_uuid = uuid.UUID(student_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                             detail="Invalid student_id format. Expected UUID.")
    now = datetime.now()
    recording_uuid = uuid.uuid4()
    webcam_path = f"{now}/{recording_uuid}_webcam{Path(webcam.filename).suffix}"
    screencast_path = f"{now}/{recording_uuid}_screencast{Path(screencast.filename).suffix}"
    await file_storage.save_upload_file(webcam, webcam_path)
    await file_storage.save_upload_file(screencast, screencast_path)
    recording = Recording(
        student_id=student_uuid,
        path_webcam=str(webcam_path),
        path_screen=str(screencast_path)
    )
    session.add(recording)
    await session.commit()
    await session.refresh(recording)
    return RecordingRead.model_validate(recording)

async def save_calibration_files(
    webcam: UploadFile,
    screencast: UploadFile
):
    now = datetime.now()
    calibration = uuid.uuid4()
    webcam_path = f"{now}/{calibration}_webcam{Path(webcam.filename).suffix}"
    screencast_path = f"{now}/{calibration}_screencast{Path(screencast.filename).suffix}"
    await file_storage.save_upload_file(webcam, webcam_path)
    await file_storage.save_upload_file(screencast, screencast_path)
    return webcam_path, screencast_path


@connection
async def mark_recording_done(
    recording_id: uuid.UUID,
    path_processed_webcam: Optional[str] = None,
    path_processed_screen: Optional[str] = None,
    session: AsyncSession = None,
):
    recording = (
        await session.execute(
            select(Recording).where(Recording.recording_id == recording_id)
        )
    ).scalar_one_or_none()
    if recording is None:
        return
    recording.status = RecordingStatus.DONE
    recording.processed_date = datetime.now(timezone.utc)
    if path_processed_webcam:
        recording.path_processed_webcam = path_processed_webcam
    if path_processed_screen:
        recording.path_processed_screen = path_processed_screen
    await session.commit()
