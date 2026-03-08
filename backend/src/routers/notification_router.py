from fastapi import APIRouter, HTTPException, status, UploadFile, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timezone

from ..models import Notification
from ..database import get_db

router = APIRouter(prefix="/notification", tags=["notification"])

@router.get("")
async def get_notifications(db: Session = Depends(get_db)):
    try:
        notifications = db.query(Notification).all()
        return JSONResponse(
            content={"notifications": [notification.to_dict() for notification in notifications]},
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get notifications: {str(e)}")

@router.delete("/{id}")
async def delete_notification(id: str, db: Session = Depends(get_db)):
    try:
        notification_uuid = uuid.UUID(id)
        notification = db.query(Notification).filter(Notification.notification_id == notification_uuid).first()
        
        if not notification:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
        
        db.delete(notification)
        db.commit()
        
        return JSONResponse(
            content={"message": "Notification deleted successfully"},
            status_code=status.HTTP_200_OK
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid notification_id format. Expected UUID.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete notification: {str(e)}")

@router.put("/{id}")
async def mark_notification_as_viewed(id: str, db: Session = Depends(get_db)):
    try:
        notification_uuid = uuid.UUID(id)
        notification = db.query(Notification).filter(Notification.notification_id == notification_uuid).first()
        
        if not notification:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
        
        notification.sent_date = datetime.now(timezone.utc)
        db.commit()
        
        return JSONResponse(
            content=notification.to_dict(),
            status_code=status.HTTP_200_OK
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid notification_id format. Expected UUID.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to mark notification as viewed: {str(e)}")