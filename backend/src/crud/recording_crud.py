import uuid

from fastapi import UploadFile, Form, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.exceptions import HTTPException

from src.config.connection import connection
from src.models import Recording


@connection
async def get_recordings(session: AsyncSession):
    recordings = session.execute(select(Recording).where(Recording.recording_id == id))
    return recordings


@connection
async def delete_recording(id: str, session: AsyncSession):
    try:
        recording_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid recording_id format. Expected UUID.")
    recording = session.execute(select(Recording).where(Recording.recording_id == recording_uuid))
    if not recording:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recording not found")
    await session.delete(recording)
    await session.commit()

@connection
async def get_recording(id: str, session: AsyncSession):
    try:
        recording_uuid = uuid.UUID(id) #TODO: PYDANTIC спасет от дублирования
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid recording_id format. Expected UUID.")
    recording = await session.execute(select(Recording).where(Recording.recording_id == recording_uuid))
    recording = recording.scalar_one_or_none()
    if recording is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"recording not found with uuid: {recording_uuid}")
    return recording

@connection
async def create_recording(    student_id: str,
    webcam: UploadFile,
    screencast: UploadFile, session: AsyncSession):

    if webcam is None or screencast is None: # TODO: PYDANTIC для валидации полей
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Expected 'webcam' and 'screencast' files.")

    print("student_id:", student_id)
    print("webcam type:", webcam.content_type)
    print("screencast type:", screencast.content_type)
    try:
        student_uuid = uuid.UUID(student_id)
    except ValueError:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                             detail="Invalid student_id format. Expected UUID.")

    recording_uuid = uuid.uuid4()
    webcam_path = f"/files/{recording_uuid}_webcam{Path(webcam.filename).suffix}"
    screencast_path = f"/files/{recording_uuid}_screencast{Path(screencast.filename).suffix}"

    recording = Recording(
        student_id=student_uuid,
        path_webcam=str(webcam_path),
        path_screen=str(screencast_path)
    )
    session.add(recording)
    await session.commit()
    await session.refresh(recording)
    return recording