import uuid
from typing import List

from fastapi import APIRouter

from src.crud import suspicious_crud
from src.schemas.suspicious_schema import SuspiciousRead

router = APIRouter(prefix="/suspicious", tags=["suspicious"])


@router.get("/{recording_id}", response_model=List[SuspiciousRead])
async def get_suspicious_intervals_by_id(recording_id: uuid.UUID):
    suspicious_intervals = await suspicious_crud.get_suspicious_intervals_by_id(recording_id)
    return suspicious_intervals
