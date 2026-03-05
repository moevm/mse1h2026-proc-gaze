from fastapi import APIRouter, HTTPException, status, UploadFile
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/suspicious", tags=["suspicious"])

@router.get("{id}")
async def get_suspicious_intervals_by_id(id: int):
    pass