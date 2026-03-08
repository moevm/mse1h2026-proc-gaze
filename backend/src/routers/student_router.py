from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import uuid
from ..models import Student
from ..database import get_db

router = APIRouter(prefix="/student", tags=["student"])

@router.get("/{id}")
async def get_student(id: str, db: Session = Depends(get_db)):
    try:
        student_uuid = uuid.UUID(id)
        student = db.query(Student).filter(Student.student_id == student_uuid).first()
        
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
        
        return JSONResponse(
            content=student.to_dict(),
            status_code=status.HTTP_200_OK
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid student_id format. Expected UUID.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get student: {str(e)}")

@router.get("")
async def get_students(db: Session = Depends(get_db)):
    try:
        students = db.query(Student).all()
        return JSONResponse(
            content={"students": [student.to_dict() for student in students]},
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get students: {str(e)}")

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
