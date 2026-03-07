from fastapi import APIRouter, HTTPException, status, UploadFile, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..models import Recording
from ..database import get_db

router = APIRouter(prefix="/recording", tags=["recording"])

@router.post("/upload")
async def handle_upload_files(webcam: UploadFile = None, screencast: UploadFile = None, db: Session = Depends(get_db)):
    if webcam is None or screencast is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Expected 'webcam' and 'screencast' files.")

    print("webcam type:", webcam.content_type)
    print("screencast type:", screencast.content_type)
    try:
        recording = Recording()
        db.add(recording)
        db.commit()
        db.refresh(recording)

        return JSONResponse(
            content={"id": str(recording.recording_id)},
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create recording")

@router.get("{id}")
async def get_recording(id: int):
    pass

@router.get("")
async def get_recordings():
    pass

@router.delete("/{id}")
async def delete_recording(id: int):
    pass
