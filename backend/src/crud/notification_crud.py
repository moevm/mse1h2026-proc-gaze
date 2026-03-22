import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.models import Notification
from src.schemas.notification_schema import NotificationCreate
from src.schemas.notification_schema import NotificationRead
from src.util.connection import connection


@connection
async def get_notifications(session: AsyncSession):
    notifications = await session.execute(select(Notification).where(Notification.sent_date is None))
    notifications = notifications.scalars().all()
    for notification in notifications:
        notification.sent_date = datetime.now(timezone.utc)
    await session.commit()
    return [NotificationRead.model_validate(notification) for notification in notifications]


@connection
async def delete_notification(id: str, session: AsyncSession):
    try:
        notification_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid notification_id format. Expected UUID.")
    response = await session.execute(select(Notification).where(Notification.notification_id == notification_uuid))
    notification = response.scalar_one_or_none()
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"notification not found with uuid: {notification_uuid}")
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
