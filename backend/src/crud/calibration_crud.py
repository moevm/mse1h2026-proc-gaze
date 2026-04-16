import uuid

from sqlalchemy import select
from starlette import status
from starlette.exceptions import HTTPException

from src.schemas.calibration_schema import CalibrationResultRead
from src.models import CalibrationResult
from src.util.connection import connection
from sqlalchemy.ext.asyncio import AsyncSession


@connection
async def create_calibration_result(calibration_result: CalibrationResultRead, session: AsyncSession):
    stmt = select(CalibrationResult).where(
        CalibrationResult.student_id == calibration_result.student_id
    )
    result = await session.execute(stmt)
    db_calibration = result.scalar_one_or_none()

    if db_calibration:
        db_calibration.result = calibration_result.result
    else:
        db_calibration = CalibrationResult(
            student_id=calibration_result.student_id,
            result=calibration_result.result
        )
        session.add(db_calibration)

    await session.commit()

@connection
async def get_calibration_result(student_id: uuid.UUID, session: AsyncSession):
    stmt = select(CalibrationResult).where(
        CalibrationResult.student_id == student_id
    )
    result = await session.execute(stmt)
    db_calibration = result.scalar_one_or_none()
    if not db_calibration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calibration not found")
    return CalibrationResultRead.model_validate(db_calibration)