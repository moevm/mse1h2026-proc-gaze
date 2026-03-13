import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.connection import connection
from models import Notification


@connection
async def get_notifications(session: AsyncSession):
    notifications = session.execute(select(Notification))
    return notifications

@connection
async def delete_notification(id: str, session: AsyncSession):
    try:
        notification_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid notification_id format. Expected UUID.")
    notification = session.execute(select(Notification).where(Notification.notification_id == notification_uuid))
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    await session.delete(notification)
    await session.commit()

@connection
async def mark_notification_as_viewed(id: str, session: AsyncSession):
    try:
        notification_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid notification_id format. Expected UUID.")
    notification = session.query(Notification).filter(Notification.notification_id == notification_uuid).first()

    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    notification.sent_date = datetime.now(timezone.utc)
    await session.commit()
