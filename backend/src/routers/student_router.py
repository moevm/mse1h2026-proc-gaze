from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from ..models import Student
from ..database import get_db

router = APIRouter(prefix="/student", tags=["student"])

@router.get("{id}")
async def get_student(id: int):
    pass

@router.get("")
async def get_students():
    pass

@router.post("")
async def create_student(db: Session = Depends(get_db)):
    try:
        student = Student()
        db.add(student)
        db.commit()
        
        return JSONResponse(
            content={"student_id": str(student.student_id)},
            status_code=status.HTTP_201_CREATED
        )
    except Exception as e:
        db.rollback()
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create student: {str(e)}")
