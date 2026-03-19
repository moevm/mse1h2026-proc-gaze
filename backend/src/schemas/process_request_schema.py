import uuid

from pydantic import BaseModel, Field


class ProcessRequest(BaseModel):
    recording_id: uuid.UUID = Field(...)
    path_webcam: str = Field(...)
    path_screen: str = Field(...)

    class Config:
        from_attributes = True