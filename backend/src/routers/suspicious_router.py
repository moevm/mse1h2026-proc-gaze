import uuid

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from ..models import SuspiciousInterval

router = APIRouter(prefix="/suspicious", tags=["suspicious"])

@router.get("/{id}")
async def get_suspicious_intervals_by_id(id: str, db: AsyncSession = Depends(get_db)):
    try:
        recording_uuid = uuid.UUID(id)
        suspicious_intervals = db.query(SuspiciousInterval).filter(
            SuspiciousInterval.recording_id == recording_uuid
        ).all()
        
        return JSONResponse(
            content={"suspicious_intervals": [interval.to_dict() for interval in suspicious_intervals]},
            status_code=status.HTTP_200_OK
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid recording_id format. Expected UUID.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get suspicious intervals: {str(e)}")