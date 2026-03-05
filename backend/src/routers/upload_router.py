from fastapi import APIRouter, Depends, HTTPException, status, Response, UploadFile
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/user", tags=["user"])

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