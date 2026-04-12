import uuid
from typing import List

from fastapi import APIRouter, status

from src.schemas.notification_schema import NotificationRead
from src.crud import notification_crud

router = APIRouter(prefix="/notification", tags=["notification"])


@router.get("", response_model=List[NotificationRead])
async def get_notifications():
    notifications = await notification_crud.get_notifications()
    return notifications


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(id: uuid.UUID):
    await notification_crud.delete_notification(id)
