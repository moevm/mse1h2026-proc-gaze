import asyncio
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Notification
from src.schemas.notification_schema import NotificationCreate
from src.schemas.notification_schema import NotificationRead
from src.util.connection import connection

notification_queue = asyncio.Queue()


@connection
async def get_notifications(session: AsyncSession):
    notifications = await session.execute(select(Notification).where(Notification.sent_date == None))
    notifications = notifications.scalars().all()
    for notification in notifications:
        notification.sent_date = datetime.now(timezone.utc).replace(tzinfo=None)
    await session.commit()
    return [NotificationRead.model_validate(notification) for notification in notifications]


@connection
async def delete_notification(notification_id: uuid.UUID, session: AsyncSession):
    response = await session.execute(select(Notification).where(Notification.notification_id == notification_id))
    notification = response.scalar_one_or_none()
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"notification not found with uuid: {notification_id}")
    await session.delete(notification)
    await session.commit()


@connection
async def create_notification(notification_create: NotificationCreate, session: AsyncSession):
    notification = Notification(
        recording_id=notification_create.recording_id,
        created_date=notification_create.created_date,
        type=notification_create.type
    )
    session.add(notification)
    await session.commit()
    await notification_queue.put(NotificationRead.model_validate(notification))
