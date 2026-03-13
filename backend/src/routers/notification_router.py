from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from src.crud import notification_crud

router = APIRouter(prefix="/notification", tags=["notification"])

@router.get("")
async def get_notifications():
    notifications = await notification_crud.get_notifications()
    return JSONResponse(
        content={"notifications": [notification.to_dict() for notification in notifications]},
        status_code=status.HTTP_200_OK
    )

@router.delete("/{id}")
async def delete_notification(id: str):
    await notification_crud.delete_notification(id)
    return JSONResponse(
        content={"message": "Notification deleted successfully"},
        status_code=status.HTTP_200_OK
    )
@router.put("/{id}")
async def mark_notification_as_viewed(id: str):
    notification = await notification_crud.mark_notification_as_viewed(id)
    return JSONResponse(
        content=notification.to_dict(),
        status_code=status.HTTP_200_OK
    )