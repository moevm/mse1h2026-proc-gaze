from fastapi import APIRouter, HTTPException, status, UploadFile
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/notification", tags=["notification"])

@router.get("")
async def get_notifications():
    pass

@router.delete("/{id}")
async def delete_notification(id: int):
    pass

@router.put("/{id}")
async def mark_notification_as_viewed(id: int):
    pass