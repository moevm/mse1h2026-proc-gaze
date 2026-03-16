import uuid
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.exceptions import HTTPException

from schemas.student_schema import StudentRead
from src.util.connection import connection
from src.models import Student


@connection
async def get_student(id: str, session: AsyncSession) -> StudentRead:
    try:
        student_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid student_id format. Expected UUID.")
    student = (await session.execute(select(Student).where(Student.student_id == student_uuid))).scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return StudentRead.model_validate(student)

@connection
async def get_students(session: AsyncSession) -> List[StudentRead]:
    result = await session.execute(select(Student))
    students = result.scalars().all()
    return [StudentRead.model_validate(student) for student in students]

@connection
async def create_student(session: AsyncSession) -> StudentRead:
    student = Student()
    session.add(student)
    await session.commit()
    await session.refresh(student)
    return StudentRead.model_validate(student)