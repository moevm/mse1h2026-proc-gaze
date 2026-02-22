from fastapi import FastAPI, UploadFile
from fastapi.responses import JSONResponse
from fastapi import status

app = FastAPI()

@app.post("/upload")
async def handle_upload_files(webcam: UploadFile = None, screencast: UploadFile = None):
    if webcam is None or screencast is None:
        return JSONResponse(
            content={"error": "Expected 'webcam' and 'screencast' files."},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    print("webcam type:", webcam.content_type)
    print("screencast type:", screencast.content_type)

    # upload videos to local storage...
    # if bad (wrong format, too big,  etc...), return error
    
    # start job...
    # if bad, remove files and return error

    return JSONResponse(
        content={'id': 12345},
        status_code=status.HTTP_200_OK
    )