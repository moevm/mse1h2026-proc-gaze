import uuid

from sqlalchemy import select, UUID
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.exceptions import HTTPException

from src.schemas.suspicious_schema import SuspiciousRead, SuspiciousResult
from src.models import SuspiciousInterval
from src.util.connection import connection


@connection
async def get_suspicious_intervals_by_id(id: str, session: AsyncSession):
    try:
        recording_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid recording_id format. Expected UUID.")

    suspicious_intervals = await session.execute(select(SuspiciousInterval).where(
        SuspiciousInterval.recording_id == recording_uuid).order_by(SuspiciousInterval.time))
    suspicious_intervals = suspicious_intervals.scalars().all()
    return [SuspiciousRead.model_validate(suspicious_interval) for suspicious_interval in suspicious_intervals]


@connection
async def save_suspicious_intervals(suspicious_result: SuspiciousResult, session: AsyncSession):
    recording_id = suspicious_result.recording_id
    intervals_to_save = []
    for interval in suspicious_result.intervals:
        suspicious_interval = SuspiciousInterval(
            recording_id=recording_id,
            time=interval.time,
            duration=interval.duration,
            description=interval.description
        )
        intervals_to_save.append(suspicious_interval)
    if intervals_to_save:
        session.add_all(intervals_to_save)
        await session.commit()