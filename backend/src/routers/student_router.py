from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from src.crud import student_crud

router = APIRouter(prefix="/students", tags=["student"])

@router.get("/{id}")
async def get_student(id: str):
    student = await student_crud.get_student(id)
    return JSONResponse(
        content=student.to_dict(),
        status_code=status.HTTP_200_OK
    )

@router.get("")
async def get_students():
    students = await student_crud.get_students()
    return JSONResponse(
        content={"students": [student.to_dict() for student in students]},
        status_code=status.HTTP_200_OK
    )


@router.post("")
async def create_student():
    student = await student_crud.create_student()
    return JSONResponse(
        content={"student_id": str(student.student_id)},
        status_code=status.HTTP_201_CREATED
    )
