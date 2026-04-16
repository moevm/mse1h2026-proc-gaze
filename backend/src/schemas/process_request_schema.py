import uuid
from typing import Optional

from pydantic import BaseModel, Field

from src.schemas.calibration_schema import CalibrationResultRead


class ProcessRequest(BaseModel):
    recording_id: uuid.UUID = Field(...)
    path_webcam: str = Field(...)
    path_screen: str = Field(...)
    calibration_result: Optional[CalibrationResultRead] = Field(None)

    class Config:
        from_attributes = True
