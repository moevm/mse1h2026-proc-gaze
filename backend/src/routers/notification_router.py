import asyncio
import uuid
from typing import List

from fastapi import APIRouter, status, Request
from fastapi.sse import EventSourceResponse

from src.crud import notification_crud
from src.crud.notification_crud import notification_manager
from src.schemas.notification_schema import NotificationRead

router = APIRouter(prefix="/notification", tags=["notification"])


@router.get("", response_model=List[NotificationRead])
async def get_notifications():
    notifications = await notification_crud.get_notifications()
    return notifications


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(notification_id: uuid.UUID):
    await notification_crud.delete_notification(notification_id)


@router.get("/stream")
async def notification_stream(request: Request):
    notification_queue = asyncio.Queue()
    notification_manager.add_connection(notification_queue)
    try:
        async def event_generator():
            while True:
                if await request.is_disconnected():
                    break
                notification = await notification_queue.get()
                yield (
                    f"event: notification\n"
                    f"data: {notification.model_dump_json()}\n\n"
                )
        return EventSourceResponse(event_generator())
    finally:
        await notification_manager.remove_connection(notification_queue)