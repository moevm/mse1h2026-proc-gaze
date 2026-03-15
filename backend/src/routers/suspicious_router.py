from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from src.crud import suspicious_crud

router = APIRouter(prefix="/suspicious", tags=["suspicious"])

@router.get("/{id}")
async def get_suspicious_intervals_by_id(id: str):
    suspicious_intervals = await suspicious_crud.get_suspicious_intervals_by_id(id)

    return JSONResponse(
        content={"suspicious_intervals": [interval.to_dict() for interval in suspicious_intervals]},
        status_code=status.HTTP_200_OK
    )