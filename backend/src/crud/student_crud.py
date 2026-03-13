import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.exceptions import HTTPException

from config.connection import connection
from models import Student


@connection
async def get_student(id: str, session: AsyncSession):
    try:
        student_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid student_id format. Expected UUID.")
    student = session.execute(select(Student).where(Student.student_id == student_uuid))
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student

@connection
async def get_students(session: AsyncSession):
    return (await session.execute(select(Student))).scalars().all()

@connection
async def create_student(session: AsyncSession):
    student = Student()
    session.add(student)
    await session.commit()