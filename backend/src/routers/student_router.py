import uuid
from typing import List

from fastapi import APIRouter, status, Form, UploadFile, HTTPException

from src.schemas.student_schema import StudentCreate, StudentRead
from src.crud import student_crud

router = APIRouter(prefix="/students", tags=["student"])


@router.get("/{id}", response_model=StudentRead, status_code=status.HTTP_200_OK)
async def get_student(id: uuid.UUID):
    student = await student_crud.get_student(id)
    return student


@router.get("", response_model=List[StudentRead], status_code=status.HTTP_200_OK)
async def get_students():
    students = await student_crud.get_students()
    return students


@router.post("", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
async def create_student(student_create: StudentCreate):
    student = await student_crud.create_student(student_create)
    return student


@router.post("/dump", response_model=List[StudentRead], status_code=status.HTTP_201_CREATED)
async def insert_student_dump(student_dump: UploadFile):
    students = await student_crud.insert_students(student_dump)
    return students