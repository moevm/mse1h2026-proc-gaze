from fastapi import APIRouter, HTTPException, status, UploadFile
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/student", tags=["student"])

@router.get("{id}")
async def get_student(id: int):
    pass

@router.get("")
async def get_students():
    pass


