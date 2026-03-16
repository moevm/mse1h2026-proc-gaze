import logging

import aiofiles
from fastapi import UploadFile
from starlette import status
from starlette.exceptions import HTTPException
from starlette.responses import FileResponse

from src.util.config import UPLOAD_DIR


async def save_upload_file(upload_file: UploadFile, destination: str) -> None:
    path = UPLOAD_DIR / destination
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        async with aiofiles.open(path, 'wb') as out_file:
            while content := await upload_file.read(1024 * 1024):
                await out_file.write(content)
    except Exception as e:
        logging.error(f"Error saving file {destination}: {e}")
        raise
    finally:
        await upload_file.close()


async def get_file(path: str) -> FileResponse:
    file_path = UPLOAD_DIR / path
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    try:
        return FileResponse(
            path=file_path,
            filename=file_path.name,
            media_type="application/octet-stream"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error sending file"
        )
