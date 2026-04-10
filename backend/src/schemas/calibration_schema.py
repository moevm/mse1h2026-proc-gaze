import uuid
from typing import List

from pydantic import BaseModel, Field, field_validator


class Click(BaseModel):
    time: float = Field(..., description="Время нажатия на круг в секундах")
    x: int = Field(..., description="Y координата круга относительно окна браузера")
    y: int = Field(..., description="X координата круга относительно окна браузера")


class CalibrationData(BaseModel):
    window_width: int = Field(..., description="Ширина окна браузера")
    window_height: int = Field(..., description="Высота окна браузера")
    screen_width: int = Field(..., description="Ширина всего экрана")
    screen_height: int = Field(..., description="Высота всего экрана")
    window_screen_x: int = Field(..., description="Положение окна браузера относительно левого верхнего края экрана по оси Y")
    window_screen_y: int = Field(..., description="Положение окна браузера относительно левого верхнего края экрана по оси X")
    clicks: List[Click] = Field(..., description="Данные кликов")


class CalibrationRead(BaseModel):
    student_id: uuid.UUID = Field(..., description="UUID студента")
    webcam_path: str = Field(..., description="Путь к видеокамере")
    screencast_path: str = Field(..., description="Путь к скринкасту")
    calibration_data: CalibrationData = Field(..., description="Данные калибровки")

class CalibrationResultRead(BaseModel):
    student_id: uuid.UUID = Field(..., description="UUID студента")
    result: List[float] = Field(..., description="Результат калибровки")

    @field_validator('result')
    @classmethod
    def validate_vector_size(cls, v: List[float]) -> List[float]:
        if len(v) != 3:
            raise ValueError(f'Vector must have exactly 3 dimensions, got {len(v)}')
        return v

    model_config = {
        "from_attributes": True
    }