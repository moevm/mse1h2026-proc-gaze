import uuid
from typing import List

from fastapi import APIRouter

from src.crud import suspicious_crud
from src.schemas.suspicious_schema import SuspiciousRead

router = APIRouter(prefix="/suspicious", tags=["suspicious"])


@router.get("/{id}", response_model=List[SuspiciousRead])
async def get_suspicious_intervals_by_id(id: uuid.UUID):
    suspicious_intervals = await suspicious_crud.get_suspicious_intervals_by_id(id)
    return suspicious_intervals
