from fastapi import APIRouter, status, UploadFile, Form
from fastapi.responses import JSONResponse

from src.crud import recording_crud

router = APIRouter(prefix="/recording", tags=["recording"])

@router.post("/upload")
async def handle_upload_files(
    student_id: str = Form(...),
    webcam: UploadFile = None,
    screencast: UploadFile = None
):
    recording = await recording_crud.create_recording(student_id, webcam, screencast)
    return JSONResponse(
        content={"id": str(recording.recording_id)},
        status_code=status.HTTP_200_OK
    )


@router.get("/{id}")
async def get_recording(id: str):
    recording = await recording_crud.get_recording(id)
    return JSONResponse(
        content=recording.to_dict(),
        status_code=status.HTTP_200_OK
    )

@router.get("")
async def get_recordings():
    recordings = await recording_crud.get_recordings()
    return JSONResponse(
        content={"recordings": [recording.to_dict() for recording in recordings]},
        status_code=status.HTTP_200_OK
    )

@router.delete("/{id}")
async def delete_recording(id: str):
    await recording_crud.delete_recording(id)
    return JSONResponse(
        content={"message": "Recording deleted successfully"},
        status_code=status.HTTP_200_OK
    )


