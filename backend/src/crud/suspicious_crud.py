import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.exceptions import HTTPException

from config.connection import connection
from models import SuspiciousInterval


@connection
async def get_suspicious_intervals_by_id(id: str, session: AsyncSession):
    try:
        recording_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid recording_id format. Expected UUID.")
    suspicious_intervals = session.execute(select(SuspiciousInterval).where(
        SuspiciousInterval.recording_id == recording_uuid))
    return suspicious_intervals
