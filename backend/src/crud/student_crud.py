import csv
import io
import uuid
from typing import List

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.exceptions import HTTPException

from src.models import Student
from src.schemas.student_schema import StudentRead, StudentCreate
from src.util.connection import connection


@connection
async def get_student(id: uuid.UUID, session: AsyncSession) -> StudentRead:
    student = (await session.execute(select(Student).where(Student.student_id == id))).scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return StudentRead.model_validate(student)


@connection
async def get_students(session: AsyncSession) -> List[StudentRead]:
    result = await session.execute(select(Student))
    students = result.scalars().all()
    return [StudentRead.model_validate(student) for student in students]


@connection
async def create_student(student_create: StudentCreate, session: AsyncSession) -> StudentRead:
    student = Student(
        first_name=student_create.first_name,
        last_name=student_create.last_name,
        patronymic=student_create.patronymic,
        group=student_create.group,
    )
    session.add(student)
    await session.commit()
    await session.refresh(student)
    return StudentRead.model_validate(student)


@connection
async def insert_students(student_dump: UploadFile, session: AsyncSession) -> List[StudentRead]:
    if not student_dump.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed"
        )
    contents = await student_dump.read()
    try:
        csv_text = contents.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be UTF-8 encoded"
        )

    try:
        csv_reader = csv.DictReader(io.StringIO(csv_text))
        expected_headers = ['first_name', 'last_name', 'group']
        actual_headers = csv_reader.fieldnames

        missing_headers = set(expected_headers) - set(actual_headers or [])
        if missing_headers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required columns: {missing_headers}"
            )

        students = []
        errors = []
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                first_name = row.get('first_name', '').strip()
                last_name = row.get('last_name', '').strip()
                patronymic = row.get('patronymic', '').strip() or None
                group = row.get('group', '').strip()

                if not first_name:
                    errors.append(f"Row {row_num}: first_name is required")
                    continue
                if not last_name:
                    errors.append(f"Row {row_num}: last_name is required")
                    continue
                if not group:
                    errors.append(f"Row {row_num}: group is required")
                    continue

                students.append(Student(
                    first_name=first_name,
                    last_name=last_name,
                    patronymic=patronymic,
                    group=group
                ))
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")

        if errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Validation errors: {'; '.join(errors[:5])}"
            )

        session.add_all(students)
        await session.commit()
        return [StudentRead.model_validate(student) for student in students]

    except csv.Error as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV parsing error: {str(e)}"
        )
