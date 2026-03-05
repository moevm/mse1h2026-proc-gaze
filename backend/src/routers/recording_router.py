from fastapi import APIRouter, HTTPException, status, UploadFile
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/recording", tags=["recording"])

@router.post("/upload")
async def handle_upload_files(webcam: UploadFile = None, screencast: UploadFile = None):
    if webcam is None or screencast is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Expected 'webcam' and 'screencast' files.")

    print("webcam type:", webcam.content_type)
    print("screencast type:", screencast.content_type)

    return JSONResponse(
        content={'id': 12345}, # just example
        status_code=status.HTTP_200_OK
    )

@router.get("{id}")
async def get_recording(id: int):
    pass

@router.get("")
async def get_recordings():
    pass

@router.delete("/{id}")
async def delete_recording(id: int):
    pass
